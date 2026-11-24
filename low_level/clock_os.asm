; nasm -f bin clock_os.asm -o clock_os.bin
; qemu-system-i386 -drive format=raw,file=clock_os.bin -rtc base=localtime
[ORG 0x7C00]    ; bios loads MBR
[BITS 16]

start:
    ; set up the stack and segments
    cli         ; disables maskable hardware interrupts
    xor ax, ax  ; set registers to 0
    mov ds, ax 
    mov es, ax 
    mov ss, ax  
    mov sp, 0x7C00 ; set stack pointer
    sti         ; allows maskable hardware interrupts

    ; clear screen
    mov ax, 0x0003
    int 0x10

main_loop:
    ; read RTC time
    mov ah, 0x02
    int 0x1A

    ; if RTC returned an error then retry
    jc main_loop

    ; rm PM indicator from hours
    and ch, 0x7F

    ; save the time values
    mov [hours], ch
    mov [minutes], cl
    mov [seconds], dh

    ; move cursor to start
    mov ah, 0x02
    mov bh, 0
    mov dx, 0
    int 0x10

    ; print "time: "
    mov si, time_msg
    call print_string

    mov al, [hours]
    call print_bcd

    mov al, ':'
    call print_char

    mov al, [minutes]
    call print_bcd

    mov al, ':'
    call print_char

    mov al, [seconds]
    call print_bcd

    ; wait 1 second
    mov ah, 0x86
    mov cx, 0x000F
    mov dx, 0x4240
    int 0x15

    jmp main_loop


; print \n
print_string:
    lodsb
    test al, al
    jz .done
    call print_char
    jmp print_string
.done:
    ret


; print one character
print_char:
    push bx         ; preserve BX
    mov ah, 0x0E   ; BIOS teletype output
    mov bh, 0      ; video page 0
    int 0x10
    pop bx          ; restore BX
    ret


; Convert and print BCD
print_bcd:
    push ax         ; preserve AX
    push bx         ; preserve BX

    ; Save original BCD value
    mov bl, al

    ; High nibble
    mov al, bl
    shr al, 4
    and al, 0x0F
    add al, '0'
    call print_char

    ; Low nibble
    mov al, bl
    and al, 0x0F
    add al, '0'
    call print_char

    pop bx          ; restore BX
    pop ax          ; restore AX
    ret


; variables
hours   db 0
minutes db 0
seconds db 0

time_msg db 'TIME: ', 0


; boot sector padding
times 510-($-$$) db 0
dw 0xAA55
