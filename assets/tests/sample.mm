//static declarations
define register_size 32;
define addr_mode byte;

//registers
register CONTROL description="Control Register";
register STATUS description="Status Register";

//register fields
field CONTROL.IRQEN position=0 access=RW description="Enable Interrupts" default=1;
field CONTROL.STOP_ON_ERR position=1 access=RW description="Stop IP on video errors" default=0;
field STATUS.IRQCLR position=7 access=RW description="Interrupt flag; write 1 to clear";
field STATUS.VIDEOERR position=0 access=R description="Video error flag";

//outputs from register bits
output IRQ_EN source=CONTROL.IRQEN;
output STOP_ON_ERROR source=CONTROL.STOP_ON_ERR;
output IRQ_ACK source=STATUS.IRQCLR;

//input flags from logic
input IRQ_FLAG dest=STATUS.IRQCLR;
input VIDEO_ERROR dest=STATUS.VIDEOERR;
