import re
from typing import Dict, List, Optional, Tuple

from lfr.antlrgen.lfr.lfrXParser import lfrXParser
from lfr.compiler.distribute.BitVector import BitVector
from lfr.compiler.distribute.distributeblock import DistributeBlock
from lfr.compiler.language.vectorrange import VectorRange
from lfr.compiler.lfrerror import ErrorType, LFRError
from lfr.lfrbaseListener import LFRBaseListener, ListenerMode

ConditionEvalResult = Tuple[int, int, str]


class DistBlockListener(LFRBaseListener):
    def __init__(self) -> None:
        super().__init__()
        self._current_dist_block: Optional[DistributeBlock] = None
        self._current_sensitivity_list = None
        self._current_state: Optional[BitVector]
        self._current_states: List[BitVector] = []
        self._current_connectivities: List[Tuple[str, str]] = []
        # This particular variable is only used for
        # figuring out the else statement
        self._accumulated_states: List[BitVector] = []
        self._current_lhs = None
        self._distribute_condition_stack_markers: List[int] = []

    def enterDistributeCondition(self, ctx: lfrXParser.DistributeConditionContext):
        self._distribute_condition_stack_markers.append(len(self.stack))

    def exitDistributeCondition(self, ctx: lfrXParser.DistributeConditionContext):
        if self._current_dist_block is None:
            raise ValueError('"_current_dist_block" is set to None')
        state_headers = self._current_dist_block.state_table.headers

        self._current_states = []
        total_state_bits = len(state_headers)
        for state_int in range(1 << total_state_bits):
            full_state = BitVector(intVal=state_int, size=total_state_bits)
            state_bits = {
                signal_id: full_state[idx] == 1
                for idx, signal_id in enumerate(state_headers)
            }
            condition_value, _, _ = self._evaluate_distribute_condition_node(
                ctx, state_bits
            )
            if condition_value == 0:
                continue
            self._current_states.append(full_state)
        self._current_state = self._current_states[0] if self._current_states else None
        stack_marker = self._distribute_condition_stack_markers.pop()
        del self.stack[stack_marker:]

    def enterDistributionBlock(self, ctx: lfrXParser.DistributionBlockContext):
        print("Entering the Distribution Block")
        self._current_dist_block = DistributeBlock()

    def exitSensitivitylist(self, ctx: lfrXParser.SensitivitylistContext):
        sentivity_list = []

        # TODO - Go through the signals and then add then to the sentivity list
        for signal in ctx.signal():
            start_index = 0
            end_index = 0
            signal_name = signal.ID().getText()

            if signal_name not in self.vectors.keys():
                self.compilingErrors.append(
                    LFRError(
                        ErrorType.SIGNAL_NOT_FOUND,
                        "Cannot find signal - {}".format(signal_name),
                    )
                )
                continue

            v = self.vectors[signal_name]

            if signal.vector() is not None:
                start_index = int(signal.vector().start.text)
                if signal.vector().end is not None:
                    end_index = int(signal.vector().end.text)
                else:
                    end_index = start_index
            else:
                start_index = v.startindex
                end_index = v.endindex

            vrange = VectorRange(v, start_index, end_index)
            sentivity_list.append(vrange)

        if self._current_dist_block is None:
            raise ValueError('"_current_dist_block" is set to None')

        self._current_dist_block.sensitivity_list = sentivity_list

    def exitDistributionBlock(self, ctx: lfrXParser.DistributionBlockContext):
        print("Exit the Distribution Block")
        # TODO - Generate the fig from the distribute block
        if self._current_dist_block is None:
            raise ValueError('"_current_dist_block" is set to None')

        if self.currentModule is None:
            raise ValueError("Current module set to none")
        self._current_dist_block.generate_fig(self.currentModule.FIG)

    def enterDistributionassignstat(
        self, ctx: lfrXParser.DistributionassignstatContext
    ):
        print("Entering the dis assign stat")
        self.listermode = ListenerMode.DISTRIBUTE_ASSIGN_STAT_MODE
        pass

    def exitDistributionassignstat(self, ctx: lfrXParser.DistributionassignstatContext):
        print("Exiting the dist assign stat")
        rhs = self.stack.pop()
        lhs = self.stack.pop()

        # Do the same connectivity as we would do this in the normal assign
        # stat and save it for current state in the distblock object
        if len(lhs) == len(rhs):
            print("LHS, RHS sizes are equal")
            for source, target in zip(rhs, lhs):
                print(source, target)
                sourceid = source.ID
                targetid = target.ID

                self._current_connectivities.append((sourceid, targetid))

        elif len(lhs) != len(rhs):
            print("LHS not equal to RHS")
            for source in rhs:
                sourceid = source.ID

                for target in lhs:
                    targetid = target.ID
                    self._current_connectivities.append((sourceid, targetid))

    def enterIfElseBlock(self, ctx: lfrXParser.IfElseBlockContext):
        # TODO - Setup the class level variables necessary to capture
        # the various states necessary for distribute blocks
        self._accumulated_states = []

    def enterIfBlock(self, ctx: lfrXParser.IfBlockContext):
        self._current_connectivities = []
        self._accumulated_states = []
        self._current_states = []

    def enterElseIfBlock(self, ctx: lfrXParser.ElseIfBlockContext):
        self._current_connectivities = []
        self._current_states = []

    def exitIfBlock(self, ctx: lfrXParser.IfBlockContext):
        # We need to go through all the current connectivities
        # and put them into the distribute block
        if not self._current_states:
            return
        if self._current_dist_block is None:
            raise ValueError('"_current_dist_block" is set to None')

        dist_block = self._current_dist_block
        for state in self._current_states:
            self._accumulated_states.append(state)
            for connectivity in self._current_connectivities:
                dist_block.set_connectivity(state, connectivity[0], connectivity[1])

    def exitElseIfBlock(self, ctx: lfrXParser.ElseIfBlockContext):
        # We need to go through all the current connectivities
        # and put them into the distribute block
        if not self._current_states:
            return

        if self._current_dist_block is None:
            raise ValueError('"_current_dist_block" is set to None')

        dist_block = self._current_dist_block
        for state in self._current_states:
            self._accumulated_states.append(state)
            for connectivity in self._current_connectivities:
                dist_block.set_connectivity(state, connectivity[0], connectivity[1])

    def enterElseBlock(self, ctx: lfrXParser.ElseBlockContext):
        self._current_connectivities = []

    def exitElseBlock(self, ctx: lfrXParser.ElseBlockContext):
        if self._current_dist_block is None:
            raise ValueError('"_current_dist_block" is set to None')

        remaining_states = self._current_dist_block.get_remaining_states(
            self._accumulated_states
        )
        for state in remaining_states:
            for connectivity in self._current_connectivities:
                self._current_dist_block.set_connectivity(
                    state, connectivity[0], connectivity[1]
                )

    @staticmethod
    def _masked_value(value: int, width: int) -> int:
        if width <= 0:
            return 0
        return value & ((1 << width) - 1)

    def _evaluate_distribute_condition_node(
        self, ctx: lfrXParser.DistributeConditionContext, state_bits: Dict[str, bool]
    ) -> ConditionEvalResult:
        return self._evaluate_distribute_or_expr(ctx.distributeOrExpr(), state_bits)

    def _evaluate_distribute_or_expr(
        self, ctx: lfrXParser.DistributeOrExprContext, state_bits: Dict[str, bool]
    ) -> ConditionEvalResult:
        exprs = ctx.distributeAndExpr()
        value, width, kind = self._evaluate_distribute_and_expr(exprs[0], state_bits)
        for idx in range(1, len(exprs)):
            rhs_value, rhs_width, _ = self._evaluate_distribute_and_expr(
                exprs[idx], state_bits
            )
            value = 1 if ((value != 0) or (rhs_value != 0)) else 0
            width = max(1, max(width, rhs_width))
            kind = "expr"
        return value, width, kind

    def _evaluate_distribute_and_expr(
        self, ctx: lfrXParser.DistributeAndExprContext, state_bits: Dict[str, bool]
    ) -> ConditionEvalResult:
        exprs = ctx.distributeBitOrExpr()
        value, width, kind = self._evaluate_distribute_bitor_expr(exprs[0], state_bits)
        for idx in range(1, len(exprs)):
            rhs_value, rhs_width, _ = self._evaluate_distribute_bitor_expr(
                exprs[idx], state_bits
            )
            value = 1 if ((value != 0) and (rhs_value != 0)) else 0
            width = max(1, max(width, rhs_width))
            kind = "expr"
        return value, width, kind

    def _evaluate_distribute_bitor_expr(
        self, ctx: lfrXParser.DistributeBitOrExprContext, state_bits: Dict[str, bool]
    ) -> ConditionEvalResult:
        exprs = ctx.distributeBitXorExpr()
        value, width, kind = self._evaluate_distribute_bitxor_expr(exprs[0], state_bits)
        for idx in range(1, len(exprs)):
            rhs_value, rhs_width, rhs_kind = self._evaluate_distribute_bitxor_expr(
                exprs[idx], state_bits
            )
            self._assert_signal_width_match(width, kind, rhs_width, rhs_kind, "|")
            width = max(width, rhs_width)
            lhs_masked = self._masked_value(value, width)
            rhs_masked = self._masked_value(rhs_value, width)
            value = lhs_masked | rhs_masked
            kind = "expr"
        return value, width, kind

    def _evaluate_distribute_bitxor_expr(
        self, ctx: lfrXParser.DistributeBitXorExprContext, state_bits: Dict[str, bool]
    ) -> ConditionEvalResult:
        exprs = ctx.distributeBitAndExpr()
        value, width, kind = self._evaluate_distribute_bitand_expr(exprs[0], state_bits)
        for idx in range(1, len(exprs)):
            rhs_value, rhs_width, rhs_kind = self._evaluate_distribute_bitand_expr(
                exprs[idx], state_bits
            )
            operator = ctx.getChild((idx * 2) - 1).getText()
            self._assert_signal_width_match(width, kind, rhs_width, rhs_kind, operator)
            width = max(width, rhs_width)
            lhs_masked = self._masked_value(value, width)
            rhs_masked = self._masked_value(rhs_value, width)
            if operator == "^":
                value = lhs_masked ^ rhs_masked
            elif operator in ("^~", "~^"):
                value = self._masked_value(~(lhs_masked ^ rhs_masked), width)
            else:
                raise NotImplementedError(
                    'distribute condition operator "{}" is not implemented'.format(
                        operator
                    )
                )
            kind = "expr"
        return value, width, kind

    def _evaluate_distribute_bitand_expr(
        self, ctx: lfrXParser.DistributeBitAndExprContext, state_bits: Dict[str, bool]
    ) -> ConditionEvalResult:
        exprs = ctx.distributeEqualityExpr()
        value, width, kind = self._evaluate_distribute_equality_expr(exprs[0], state_bits)
        for idx in range(1, len(exprs)):
            rhs_value, rhs_width, rhs_kind = self._evaluate_distribute_equality_expr(
                exprs[idx], state_bits
            )
            self._assert_signal_width_match(width, kind, rhs_width, rhs_kind, "&")
            width = max(width, rhs_width)
            lhs_masked = self._masked_value(value, width)
            rhs_masked = self._masked_value(rhs_value, width)
            value = lhs_masked & rhs_masked
            kind = "expr"
        return value, width, kind

    def _evaluate_distribute_equality_expr(
        self, ctx: lfrXParser.DistributeEqualityExprContext, state_bits: Dict[str, bool]
    ) -> ConditionEvalResult:
        exprs = ctx.distributePrimary()
        value, width, kind = self._evaluate_distribute_primary(exprs[0], state_bits)
        for idx in range(1, len(exprs)):
            rhs_value, rhs_width, rhs_kind = self._evaluate_distribute_primary(
                exprs[idx], state_bits
            )
            operator = ctx.getChild((idx * 2) - 1).getText()
            self._assert_signal_width_match(
                width, kind, rhs_width, rhs_kind, operator
            )
            compare_width = max(width, rhs_width)
            lhs_masked = self._masked_value(value, compare_width)
            rhs_masked = self._masked_value(rhs_value, compare_width)
            if operator == "==":
                value = 1 if lhs_masked == rhs_masked else 0
            elif operator == "!=":
                value = 1 if lhs_masked != rhs_masked else 0
            else:
                raise NotImplementedError(
                    'distribute condition operator "{}" is not implemented'.format(
                        operator
                    )
                )
            width = 1
            kind = "expr"
        return value, max(1, width), kind

    def _evaluate_distribute_primary(
        self, ctx: lfrXParser.DistributePrimaryContext, state_bits: Dict[str, bool]
    ) -> ConditionEvalResult:
        if ctx.distributeCondition() is not None:
            return self._evaluate_distribute_condition_node(
                ctx.distributeCondition(), state_bits
            )

        if ctx.number() is not None:
            value, width = self._parse_condition_number(ctx.number().getText())
            return value, width, "literal"

        if ctx.variables() is not None:
            signal_ids = self._get_signal_ids_from_variables_ctx(ctx.variables())
            self._assert_signals_in_sensitivity(signal_ids, state_bits)
            value = self._extract_vector_value_from_state(signal_ids, state_bits)
            return value, len(signal_ids), "signal"

        raise NotImplementedError(
            "unsupported distribute primary in condition evaluator"
        )

    def _get_signal_ids_from_variables_ctx(
        self,
        variables_ctx: lfrXParser.VariablesContext,
    ) -> List[str]:
        vectorvar_ctx = variables_ctx.vectorvar()
        if vectorvar_ctx is None:
            raise NotImplementedError(
                "distribute condition currently supports vectorvar operands only"
            )
        signal = vectorvar_ctx.ID().getText()
        if signal not in self.vectors:
            raise ValueError(
                "distribute condition signal '{}' is not declared".format(signal)
            )

        vector = self.vectors[signal]
        if vectorvar_ctx.vector() is None:
            start = vector.startindex
            end = vector.endindex
        else:
            start = int(vectorvar_ctx.vector().start.text)
            if vectorvar_ctx.vector().end is None:
                end = start
            else:
                end = int(vectorvar_ctx.vector().end.text)

        selected_range = VectorRange(vector, start, end)
        return [selected_range[i].ID for i in range(len(selected_range))]

    @staticmethod
    def _assert_signals_in_sensitivity(
        signal_ids: List[str], state_bits: Dict[str, bool]
    ) -> None:
        for signal_id in signal_ids:
            if signal_id not in state_bits:
                raise ValueError(
                    "distribute condition signal '{}' must be in sensitivity list".format(
                        signal_id
                    )
                )

    @staticmethod
    def _assert_signal_width_match(
        lhs_width: int,
        lhs_kind: str,
        rhs_width: int,
        rhs_kind: str,
        operator: str,
    ) -> None:
        if lhs_kind == "signal" and rhs_kind == "signal" and lhs_width != rhs_width:
            raise ValueError(
                "distribute condition signal widths do not match for operator '{}': {} vs {}".format(
                    operator, lhs_width, rhs_width
                )
            )

    @staticmethod
    def _extract_vector_value_from_state(
        signal_ids: List[str], state_bits: Dict[str, bool]
    ) -> int:
        value = 0
        for idx, signal_id in enumerate(signal_ids):
            if state_bits.get(signal_id, False):
                value |= 1 << idx
        return value

    @staticmethod
    def _parse_condition_number(text: str) -> Tuple[int, int]:
        sanitized = text.replace("_", "")
        based_match = re.fullmatch(
            r"(?:(\d+))?'([sS])?([bBoOdDhH])([0-9a-fA-FxXzZ?]+)", sanitized
        )
        if based_match is not None:
            explicit_width_text = based_match.group(1)
            base = based_match.group(3).lower()
            digits = based_match.group(4)
            normalized_digits = re.sub(r"[xXzZ?]", "0", digits)
            base_map = {"b": 2, "o": 8, "d": 10, "h": 16}
            value = int(normalized_digits, base_map[base])
            if explicit_width_text is not None:
                width = int(explicit_width_text)
            else:
                if base == "b":
                    width = len(digits)
                elif base == "o":
                    width = len(digits) * 3
                elif base == "h":
                    width = len(digits) * 4
                else:
                    width = max(1, value.bit_length())
            return value, max(1, width)

        if re.fullmatch(r"[0-9]+", sanitized):
            value = int(sanitized, 10)
            return value, max(1, value.bit_length())

        if re.fullmatch(r"[0-9]+\.[0-9]+", sanitized):
            value = float(sanitized)
            if not value.is_integer():
                raise NotImplementedError(
                    "distribute condition RHS real literals are not supported"
                )
            int_value = int(value)
            return int_value, max(1, int_value.bit_length())

        raise NotImplementedError(
            "unsupported distribute number literal '{}'".format(text)
        )

    def enterCaseBlock(self, ctx: lfrXParser.CaseBlockContext):
        self._accumulated_states = []
        self._current_state = None
        self._current_states = []

    def exitCaseBlockHeader(self, ctx: lfrXParser.CaseBlockHeaderContext):
        lhs = self.stack.pop()
        self._current_lhs = lhs

    def enterCasestat(self, ctx: lfrXParser.CasestatContext):
        self._current_connectivities = []

    def exitCasestat(self, ctx: lfrXParser.CasestatContext):
        rhs = self.stack.pop()
        assert isinstance(rhs, BitVector)
        lhs = self._current_lhs

        if self._current_dist_block is None:
            raise ValueError('"_current_dist_block" is set to None')

        dist_block = self._current_dist_block
        rhs_list = [rhs[i] == 1 for i in range(len(rhs))]
        if lhs is None:
            raise ValueError("LHS set to none in case stat")
        state_vector = self._current_dist_block.generate_state_vector([lhs], rhs_list)
        self._current_state = state_vector
        self._current_states = [state_vector]

        for connectivity in self._current_connectivities:
            dist_block.set_connectivity(
                self._current_state, connectivity[0], connectivity[1]
            )
