//static declarations
#register_size 32;

//registers
register CONTROL;
register STATUS;

//register fields
field CONTROL.IRQEN position=0 access=RW description="Enable Interrupts";
