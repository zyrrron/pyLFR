DEVICE dropletspacer

LAYER FLOW

PORT p_oil_in portRadius=2000;

DROPLET SPACER default_component;

CHANNEL c_oil_in from p_oil_in 1 to default_component 2 channelWidth=400;

END LAYER