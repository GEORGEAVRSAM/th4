; Πρόγραμμα αυτοελέγχου του TH-4: δοκιμάζει όλες τις εντολές και τον timer.
; Σωστή σειρά στη θύρα εξόδου: 8, 4, 10, 12, 2, 6, 10, 7, 9
        LOAD 5
        ADD 3           ; A = 8
        OUT             ; έξοδος = 8
        SUB 8           ; A = 0, Z = 1
        JZ ok1          ; πρέπει να πηδήξει
        JUMP fail
ok1:    LOAD 12
        AND 6           ; 1100 & 0110 = 0100
        OUT             ; έξοδος = 4
        IN              ; θύρα εισόδου = 10
        OUT             ; έξοδος = 10
        STORE 3         ; RAM[3] = 10
        LOAD 2
        STORE 7         ; RAM[7] = 2
        LOADM 3         ; A = 10
        ADDM 7          ; A = 12
        OUT             ; έξοδος = 12
        SUBM 3          ; A = 2
        OUT             ; έξοδος = 2
        SUBM 7          ; A = 0, Z = 1
        JNZ fail        ; ΔΕΝ πρέπει να πηδήξει
        LDB 3           ; B = 3
        LOAD 0
lp1:    ADD 2           ; τρεις φορές -> A = 6
        DECB
        JNZ lp1
        OUT             ; έξοδος = 6
        LOAD 2
        TAB             ; B = 2
        LOAD 0
lp2:    ADD 5           ; δύο φορές -> A = 10
        DECB
        JNZ lp2
        OUT             ; έξοδος = 10
        LOAD 1          ; Z = 0
        JZ fail         ; ΔΕΝ πρέπει να πηδήξει
        JNZ ok2         ; πρέπει να πηδήξει
        JUMP fail
ok2:    LOAD 7
        OUT             ; έξοδος = 7
        WAIT 1          ; περίμενε τον timer (1024 παλμούς)
        WAIT 1          ; και άλλους 1024
        LOAD 9
        OUT             ; έξοδος = 9
end:    JUMP end
fail:   LOAD 15
        OUT             ; 15 = κάτι πήγε στραβά
stop:   JUMP stop
