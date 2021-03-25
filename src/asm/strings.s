; -----------------------------------------------------------------------------
; This example shows how to declare and use static strings (MacOS syscalls).
;
;     nasm -f macho64 strings.s
;     ld -e start -static -o strings strings.o
;     ./strings
; -----------------------------------------------------------------------------

          global    start

          section   .text
start:
          push      20                    ; IR_MAKE_NUMBER(20)
          mov       rax, _str_001         ; IR_MAKE_STRING("Keely is een leukie\n")
          push      rax
          call      print                 ; IR_CALL_FUNCTION(..)

          mov       rax, 0x02000001       ; system call for exit
          xor       rdi, rdi              ; exit code 0
          syscall                         ; invoke operating system to exit

print:
          push      rbp                   ; Save old rbp value to stack
                                          ; Repeat this for all relevant registers
          mov       rbp, rsp              ; Save stack pointer to rbp
          sub       rsp, 8                ; rbp value is 8 bytes

          mov       rax, 0x02000004
          mov       rdi, 1
          mov       rsi, [rbp+16]
          mov       rdx, [rbp+24]
          syscall

          mov       rsp, rbp              ; Restore rsp
          pop       rbp                   ; Restore rbp
          ret                             ; Return

          section   .data
_str_001:
          db        "Keely is een leukie", 10
