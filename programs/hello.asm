;
	.title 'Z80 CP/M Hello world'

;	aseg
	org 100h

start:
	ld	hl,(6)
	ld	sp,hl
	
main:
	ld	e,'Z'
	ld	c,2
	call $0005
	ld	e,'8'
	ld	c,2
	call $0005
	ld	e,'0'
	ld	c,2
	call $0005

	ld	de,msg1
	ld	c,9
	call $0005

	ld	e,'.'
	ld	c,2
	call $0005
	ld	e,'.'
	ld	c,2
	call $0005
	ld	e,'.'
	ld	c,2
	call $0005

	ld	de,msg2
	ld	c,9
	call $0005

done:
	jp	0


msg1:	db	' Hello world','$'
msg2:	db	' Z80!',10,13,'$'

;	org	100h
;; hack to use high bits of
;; address bus as a display!
;	JP $5A03 ; Z
;	JP $3806 ; 8
;	JP $3009 ; 0
;	JP $200C ; 
;	JP $480F ; H
;	JP $4512 ; E
;	JP $4C15 ; L
;	JP $4C18 ; L
;	JP $4F1B ; O
;	JP $0000
