; -----------------------------------------------------------------------------
; This example shows how a function call is structured (MacOS syscalls).
;
;     nasm -f macho64 function.s
;     ld -e start -static -o function function.o
;     ./function; echo $?
; -----------------------------------------------------------------------------

        global start

        section .text
start:
        push    2                       ; Push two params, last param pushed first
        push    3                       ;
        call    add2                    ; Call the function

        push    rax                     ; And increase by another 64
        push    64
        call    add2

        mov     rdi, rax                ; move rax (returned value) to rdi ($?)
        mov     rax, 0x2000001          ; exit
        syscall

add2:
        push    rbp                     ; Save old rbp value to stack
                                        ; Repeat this for all relevant registers
        mov     rbp, rsp                ; Save stack pointer to rbp
        sub     rsp, 8                  ; rbp value is 8 bytes

        mov     rbx, [rbp+16]           ; Move params to registers
        mov     rax, [rbp+24]
        add     rax, rbx                ; rax := rax + rbx

        mov     rsp, rbp                ; Restore rsp
        pop     rbp                     ; Restore rbp
        ret                             ; Return
