//static declarations
#register_size 32;
#addr_mode byte;

//registers
register CONTROL;
register STATUS;

//register fields
field CONTROL.IRQEN position=0 access=RW description="Enable Interrupts";
field CONTROL.STOP_ON_ERR position=1 access=RW description="Stop IP on video errors";
field STATUS.IRQCLR position=7 access=RW description="Interrupt flag; write 1 to clear";

//outputs from register bits
output IRQ_EN source=CONTROL.IRQEN;
output STOP_ON_ERROR source=CONTROL.STOP_ON_ERROR;
output IRQ_ACK source=STATUS.IRQCLR;
