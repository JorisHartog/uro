; -------------------------------------------------------------------------------
; This example shows how a Hello World program in uro should be compiled. Runs on
; 64-bit Linux only.
;
; Syscall list: /usr/include/asm-generic/unistd.h
;
;     nasm -felf64 hello.s
;     gcc -no-pie hello.o -o hello
;     ./hello
; -------------------------------------------------------------------------------

          global    main

          extern    malloc
          extern    puts

          section   .text
main:
          mov       rbp, rsp              ; Save stack pointer

          mov       rax, f_000001         ; IR_EXTERN("malloc", 1)
          push      rax                   ;

          mov       rax, f_000002         ; IR_EXTERN("puts", 1)
          push      rax                   ;

                                          ; IR_MAKE_STRING("Keely is een leukie")
          push      20                    ;   IR_MAKE_INTEGER(20)
          call      [rbp-8]               ;   IR_CALL_FUNCTION(malloc, 20)
          add       rsp, 8                ;
          push      rax                   ;
          mov       rdi, s_000001         ;   Copy string to heap
          mov       rcx, 20               ;
          xor       rbx, rbx              ;
l_000001:                                 ;
          mov       bl, byte [rdi]        ;
          mov       byte [rax], bl        ;
          inc       rax                   ;
          inc       rdi                   ;
          dec       rcx                   ;
          cmp       rcx, byte 0           ;
          je        e_000001              ;
          jmp       l_000001              ;
e_000001:                                 ;

          call      [rbp-16]              ; IR_CALL_FUNCTION(puts, <string>)
          add       rsp, 8                ;
          push      rax                   ;

          push      0                     ; exit(0)
          call      exit                  ;

f_000001:                                 ; IR_EXTERN("malloc", 1)
          push      rbp
          push      rdi
          mov       rbp, rsp

          mov       rdi, [rbp+24]
          call      malloc

          mov       rsp, rbp
          pop       rdi
          pop       rbp
          ret

f_000002:                                 ; IR_EXTERN("puts", 1)
          push      rbp
          push      rdi
          mov       rbp, rsp

          mov       rdi, [rbp+24]
          call      puts

          mov       rsp, rbp
          pop       rdi
          pop       rbp
          ret

exit:
          mov       rax, 60               ; system call for exit
          mov       rdi, [rsp+8]          ; exit code 0
          syscall                         ;

          section   .data
s_000001:
          db        "Keely is een leukie", 0
