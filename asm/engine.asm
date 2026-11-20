; Benkei Gaiden: Suna no Shou (SNES) - Phase 4 LoROM Expansion & 8x16 VWF Engine
; Asar 1.91 (`asar --fix-checksum=off asm/engine.asm <out.sfc>`)
lorom

; ============================================================================
; Low-WRAM Scratch ($7E:1E40..$1E5F - verified zero refs in ROM & .mss)
; ============================================================================
!VWF_BUF    = $1E40  ; 16 bytes (8 words): 1bpp 8x16 accumulator tile
!VWF_PX     = $1E50  ; word: current pixel x offset in !VWF_BUF (0..7)
!VWF_DIRTY  = $1E52  ; word: non-zero if !VWF_BUF holds unemitted advance/pixels
!VWF_MODE   = $1E54  ; word: 0 = immediate ($1A80), 1 = paged ($1B80)
!VWF_STR_Y  = $1E56  ; word: saved Y index into [$A0],Y
!VWF_GLYPH  = $1E58  ; word: glyph * 16 byte offset
!VWF_WIDTH  = $1E5A  ; word: current glyph advance width (1..8)
!VWF_TMP    = $1E5C  ; word: scratch / cache candidate ID ($4000..$7FFF)
!VWF_TMP2   = $1E5E  ; word: scratch (old_px / column loop)

!PartyNames_Table = $30A900  ; Written by build.py (5 x uint16 offsets + $FF-strings)
!RedirectTables   = $30B000  ; Written by build.py (4 x (base, count) + sorted 6B entries)

; ============================================================================
; Header Expansion & Hardcoded $1D Table Bank Patches
; ============================================================================
org $00FFD7
  db $0C                     ; 2 MiB LoROM ($00-$3F)

; Widen Title Start/Continue window by 1 tile ($00:8095 w=8 -> 9) so "New Game" (47px) clears right border
org $008095
  db $09

; Bank $31: 6 sentinel name tables (tbl_equip/items/jutsu/ougi/enemies/locations)
org $00AF77 : db $31
org $00AF7D : db $31
org $00AF87 : db $31
org $00B440 : db $31
org $00B47A : db $31
org $00BEDC : db $31
org $00BEE2 : db $31
org $00BEEC : db $31
org $00D01E : db $31
org $0B8F6F : db $31
org $0B8F76 : db $31
org $0CA3F5 : db $31
org $0CA3FC : db $31
org $0CA4A5 : db $31
org $0CA4AC : db $31
org $0CA6FC : db $31
org $0CA6FF : db $31
org $0CA702 : db $31
org $0CB89E : db $31
org $0CBB49 : db $31
org $0CBB84 : db $31
org $0CBF14 : db $31
org $0CC137 : db $31
org $0CC82F : db $31
org $0CC835 : db $31
org $0CC83B : db $31
org $0CC841 : db $31
org $0CCA46 : db $31
org $0CF7FA : db $31
org $0CF81C : db $31

; Bank $32: 3 sentinel description tables (tbl_equip/items/jutsu_desc)
org $00B49D : db $32
org $00B4D2 : db $32
org $0CBDCA : db $32

; Location banner 2x scaler ($0B:8F7B was JSL $00:EC06; point directly to bank $31)
org $0B8F7B
  jsl SetBank31

; Convert 16x32 scaler ($0B:901C) to 8x32 so banners/credits double capacity without distortion
org $0B8F90
  jsl Hook_0B8F90            ; replaces SEC : LDA #$10 : SBC $B0 -> (#$20 - $B0) >> 1
  nop

org $0B8FB3
  nop : nop : nop            ; replaces duplicate JSR $8FBB (1 column per glyph, not 2)

org $0B901C
Scaler8x32:
  php
  rep #$20
  asl a
  asl a
  asl a
  asl a                      ; glyph * 16 (caller keeps B=0 for 1-byte chars)
  tax
  sep #$20
  inc $B0                    ; 1 tilemap column per 8x16 glyph
  lda #$10                   ; 16 source rows -> 32 output scanlines (4 vertical tiles)
.row_loop:
  pha
  phx
  lda.l $7E2000,X            ; 1bpp 8px row (M=1)
  rep #$20
  and #$00FF
  tay                        ; Y = row byte (preserved across $0B:9073)
  ldx $AC
  inc $AC
  jsr $9073                  ; scanline copy 1 (returns M=0)
  ldx $AC
  inc $AC
  jsr $9073                  ; scanline copy 2 (returns M=0)
  sep #$20
  plx
  inx
  pla
  dec a
  bne .row_loop
  plp
  rts
assert pc() <= $0B9059

; Shop/Kanji-picker reader in bank $01 ($01:A4DB was LDA #$001D : STA $02)
org $01A4DB
  jsl Hook_01A4DB
  nop

; Name Entry custom-name confirm copier ($01:A2A2) -> proportional renderer + Sound Test password ($01:A34E)
org $01A2A2
  jml Hook_01A2A2
  nop

org $01A34E
  db "MUSIC", $10, $FF        ; replaces JP Sound Test password (音楽会)

; Enemy name stripper ($0C:CD11): stop on either ptr[i+1]-ptr[i] OR $1E furigana
org $0CCD11
  jml Hook_CD11

; Battle command/HUD string copier ($0C:CB0A) & battle-init pre-cache copier ($0C:CF25)
org $0CCB0A
  jml Hook_CB0A

org $0CCF25
  jml Hook_CF25

; Bank $0C battle message particle bytes ($46/$39/$38/$35/$57 -> $20 ASCII space)
org $0CA5E5 : db $20
org $0CA618 : db $20
org $0CA622 : db $20
org $0CA8B8 : db $20
org $0CA8BB : db $20
org $0CA914 : db $20
org $0CA97D : db $20
org $0CA980 : db $20
org $0CA98B : db $20
org $0CA98E : db $20
org $0CA999 : db $20
org $0CA99C : db $20
org $0CA9C5 : db $20

; ============================================================================
; Core Bank $00 Text Engine & Font Hooks
; ============================================================================
org $00EC06
  jml Hook_EC06

org $00CFDF
  jml Hook_CFDF

org $00D043
  jml Hook_D043

org $00E9A3
  jml Hook_E9A3

org $00ED80
  jml Hook_ED80

org $00F4D9
  jml Hook_F4D9

org $00F573
  jml Hook_F573

; ============================================================================
; Bank $30: Relocated Code ($30:8000..$30:9FFF) & Font/Tables ($30:A000..FFFF)
; ============================================================================
org $308000

SetBank31:
  php
  sep #$20
  lda #$31
  sta $A2
  plp
  rtl

; Centers 8x32 location banners ($0B:8F90): returns X-tile offset = (32 - $B0) >> 1 with M=1.
Hook_0B8F90:
  sec
  lda #$20
  sbc $B0
  bcs .ok
  lda #$00
.ok:
  lsr a
  rtl

; ----------------------------------------------------------------------------
; LookupRedirect:
;   Input:  M=0, X=0; A = 16-bit orig address; X = bank index (0=$1A,2=$1B,4=$1C,6=$1D)
;   Output: Carry=1 -> A = new 16-bit addr, Y = new 16-bit bank (low byte)
;           Carry=0 -> not found (A preserved)
;   Clobbers: X, Y, $00..$07? NO! Uses ONLY $48..$4F? No, uses stack + regs cleanly (no DP writes)!
;   Actually saves caller's A in Y? Wait - cleaner: pass A=orig_addr, X=bank_idx, use stack slots:
;     1,S = target_addr, 3,S = lo, 5,S = hi, 7,S = table_base
; ----------------------------------------------------------------------------
LookupRedirect:
  pha                        ; keep orig_addr safely on stack (7,S later)
  lda.l !RedirectTables+8,X  ; count
  beq .not_found_pop
  dec a                      ; hi = count - 1
  pha                        ; hi
  lda #$0000
  pha                        ; lo = 0
  lda.l !RedirectTables,X    ; table byte offset from !RedirectTables
  pha                        ; base
  ; Stack (1-based): 1,S=base  3,S=lo  5,S=hi  7,S=target
.bs_loop:
  lda 3,S                    ; lo
  cmp 5,S
  beq .bs_cont
  bcs .bs_miss
.bs_cont:
  clc
  adc 5,S                    ; lo + hi
  lsr a                      ; mid = (lo + hi) >> 1
  tay                        ; Y = mid
  asl a                      ; mid * 2
  pha                        ; 1,S = 2*mid  (base shifts to 3,S)
  asl a                      ; mid * 4
  clc
  adc 1,S                    ; mid * 6
  adc 3,S                    ; base + mid * 6
  tax                        ; X = byte offset in !RedirectTables
  pla                        ; restore stack: 1,S=base 3,S=lo 5,S=hi 7,S=target
  lda.l !RedirectTables,X
  cmp 7,S
  beq .bs_hit
  bcc .bs_go_right
  ; target < table[mid] -> hi = mid - 1
  tya
  beq .bs_miss               ; mid == 0, avoid underflow!
  dec a
  sta 5,S
  bra .bs_loop
.bs_go_right:
  ; target > table[mid] -> lo = mid + 1
  tya
  inc a
  sta 3,S
  bra .bs_loop
.bs_hit:
  lda.l !RedirectTables+4,X  ; new_bank
  and #$00FF
  tay
  lda.l !RedirectTables+2,X  ; new_addr
  tax
  pla                        ; pop base
  pla                        ; pop lo
  pla                        ; pop hi
  pla                        ; pop orig_addr
  txa                        ; A = new_addr, Y = new_bank
  sec
  rts
.bs_miss:
  pla                        ; base
  pla                        ; lo
  pla                        ; hi
.not_found_pop:
  pla                        ; A = orig_addr
  clc
  rts

; ----------------------------------------------------------------------------
; Hook_EC06: Resolve $A0:$A1 + WRAM $7E:0D00 -> $A0..$A2 (with relocated lookup)
; ----------------------------------------------------------------------------
Hook_EC06:
  php
  phb
  rep #$30
  pha
  phx
  phy

  lda $A0                    ; 16-bit raw ptr
  tax                        ; save raw ptr in X
  lda.l $7E0D00
  and #$0080
  bne .act2
  ; Act 1
  txa
  cmp #$8000
  bcs .act1_hi
  ora #$8000
  ldy #$001B
  ldx #$0002                 ; bank idx 2 ($1B)
  bra .do_lookup
.act1_hi:
  cmp #$A800
  bcs .shared_1d
  ldy #$001A
  ldx #$0000                 ; bank idx 0 ($1A)
  bra .do_lookup
.act2:
  txa
  cmp #$8000
  bcs .shared_1d
  ora #$8000
  ldy #$001C
  ldx #$0004                 ; bank idx 4 ($1C)
  bra .do_lookup
.shared_1d:
  ldy #$001D
  ldx #$0006                 ; bank idx 6 ($1D)

.do_lookup:
  phy                        ; save fallback orig_bank
  jsr LookupRedirect         ; preserves Y=new_bank if C=1, else A=orig_addr
  bcs .mapped
  ply                        ; fallback orig_bank
  bra .store_ptr
.mapped:
  plx                        ; discard fallback orig_bank
.store_ptr:
  sta $A0                    ; new 16-bit addr (orig if unmapped)
  sep #$20
  tya
  sta $A2                    ; new bank (orig if unmapped)
  rep #$20

  ply
  plx
  pla
  plb
  plp
  rtl

; ----------------------------------------------------------------------------
; Hook_01A4DB: Relocates bank $1D addr in DP $00 -> $00/$02 for $01:A4D0 kanji picker
; ----------------------------------------------------------------------------
Hook_01A4DB:
  php
  rep #$30
  pha
  phx
  phy
  lda $00
  ldx #$0006                 ; bank $1D
  jsr LookupRedirect
  bcs .found
  lda #$001D
  sta $02
  bra .done
.found:
  sta $00
  tya
  and #$00FF
  sta $02
.done:
  ply
  plx
  pla
  plp
  rtl

; ----------------------------------------------------------------------------
; CopyStrTo1E80_FromX:
;   Input: X = $1D string offset, Y = dest index in $7E:1E80 (0 or append offset)
;   Saves/restores DP $00..$02 cleanly! Works regardless of caller DBR!
; ----------------------------------------------------------------------------
CopyStrTo1E80_FromX:
  rep #$30
  lda $00
  pha
  lda $02
  pha
  txa                        ; A = orig $1D addr
  ldx #$0006
  jsr LookupRedirect
  bcs .got_loc
  ldy #$001D
.got_loc:
  sta $00                    ; $00-$01 = new_addr
  tya
  sep #$20
  sta $02                    ; $02 = new_bank
  rep #$20
  ldy #$0000
  lda.l $7E0000+!VWF_TMP
  tax                        ; X = dst offset into $7E:1E80
  sep #$20
.cp_loop:
  lda [$00],Y
  sta.l $7E1E80,X
  iny
  inx
  cmp #$F0
  bcc .cp_loop
  cmp #$F8
  bcc .cp_two
  cmp #$FF
  beq .cp_done
  bra .cp_loop
.cp_two:
  lda [$00],Y
  sta.l $7E1E80,X
  iny
  inx
  bra .cp_loop
.cp_done:
  rep #$20
  pla
  sta $02
  pla
  sta $00
  rts

Hook_CFDF:
  php
  rep #$30
  pha
  phx
  phy
  lda #$0000
  sta.l $7E0000+!VWF_TMP     ; dst offset = 0
  jsr CopyStrTo1E80_FromX
  ply
  plx
  pla
  plp
  jml $00D012                ; RTS in bank $00

Hook_D043:
  php
  rep #$30
  pha
  phx
  phy
  phx                        ; save orig $1D addr (X)
  sep #$20
  ldx #$0000
.find_end:
  lda.l $7E1E80,X
  inx
  cmp #$F0
  bcc .find_end
  cmp #$F8
  bcc .skip_two
  cmp #$FF
  beq .at_end
  bra .find_end
.skip_two:
  inx
  bra .find_end
.at_end:
  dex                        ; overwrite trailing $FF
  rep #$20
  txa
  sta.l $7E0000+!VWF_TMP     ; dst offset in $7E:1E80
  plx                        ; restore X = orig $1D addr
  jsr CopyStrTo1E80_FromX
  ply
  plx
  pla
  plp
  jml $00D093                ; RTS in bank $00

; ----------------------------------------------------------------------------
; Hook_CD11: Enemy name copier ($0C:CD11 -> bank $31, stop at len OR $1E)
; ----------------------------------------------------------------------------
Hook_CD11:
  rep #$20
  and #$00FF
  asl a
  tax
  lda.l $31B93F,X
  sec
  sbc.l $31B93D,X
  pha                        ; 1,S = length in bytes
  lda.l $31B93D,X
  sta $A8
  lda #$0031
  sta $AA
  tyx                        ; X = caller-provided dst offset in $7E:1E80
  ldy #$0000
.loop:
  tya
  cmp 1,S
  bcs .done_m0
  sep #$20
  lda [$A8],Y
  cmp #$F0
  bcs .two
  cmp #$1E
  beq .done_m1
  sta.l $7E1E80,X
  inx
  iny
  rep #$20
  bra .loop
.two:
  sta.l $7E1E80,X
  inx
  iny
  lda [$A8],Y
  sta.l $7E1E80,X
  inx
  iny
  rep #$20
  bra .loop
.done_m1:
  rep #$20
.done_m0:
  pla                        ; pop length (M=0)
  sep #$20
  lda #$FF
  sta.l $7E1E80,X
  jml $0CCD48

; ----------------------------------------------------------------------------
; Hook_CB0A: Redirects $1D addr in ($AA,$A8) and copies into $7E:1E80,Y
;   Entry: X=0 (M=0 or M=1), Y = dst offset in $7E:1E80, $A8/$AA = src ptr
;   Exit:  M=1, X=0, $AA preserved, X = offset AFTER $FF, -> $0C:CB2E RTS
; ----------------------------------------------------------------------------
Hook_CB0A:
  sep #$20
  lda $AA
  pha                        ; save 1B caller $AA on stack
  rep #$20
  phy                        ; save 2B caller dst offset in $7E:1E80
  lda $AA
  and #$00FF
  cmp #$001D
  bne .no_redir
  lda $A8
  ldx #$0006                 ; bank $1D
  jsr LookupRedirect
  bcc .no_redir
  sta $A8
  sep #$20
  tya
  sta $AA
  rep #$20
.no_redir:
  plx                        ; X = dst offset in $7E:1E80
  ldy #$0000
  sep #$20
.loop:
  lda [$A8],Y
  iny
  sta.l $7E1E80,X
  inx
  cmp #$FF
  beq .done
  inc $179A                  ; matches stock $0C:CB1B
  cmp #$F0
  bcc .loop
  lda [$A8],Y
  iny
  sta.l $7E1E80,X
  inx
  inc $179A
  bra .loop
.done:
  pla                        ; restore 1B caller $AA
  sta $AA
  jml $0CCB2E

; ----------------------------------------------------------------------------
; Hook_CF25: Battle-init pre-cache copier ($0C:CD60..$CDB8)
;   Redirects $1D addr in ($AA,$A8), copies string into $7E:1E80 + $AB,
;   appends $FB (VWF flush separator) and trailing $FF, preserves caller $AA,
;   updates $AB to point at $FF, exits -> $0C:CF44 RTS.
; ----------------------------------------------------------------------------
Hook_CF25:
  sep #$20
  lda $AA
  pha                        ; save 1B caller $AA ($0C:CD6D loop keeps $AA=$1D!)
  rep #$20
  lda $AA
  and #$00FF
  cmp #$001D
  bne .no_redir
  lda $A8
  ldx #$0006                 ; bank $1D
  jsr LookupRedirect
  bcc .no_redir
  sta $A8
  sep #$20
  tya
  sta $AA
  rep #$20
.no_redir:
  ldx $AB
  ldy #$0000
  sep #$20
.loop:
  lda [$A8],Y
  iny
  cmp #$FF
  beq .end_str
  sta.l $7E1E80,X
  inx
  cmp #$F0
  bcc .loop
  lda [$A8],Y
  iny
  sta.l $7E1E80,X
  inx
  bra .loop
.end_str:
  lda #$FB                   ; internal VWF flush separator (handled by Hook_E9A3)
  sta.l $7E1E80,X
  inx
  lda #$FF
  sta.l $7E1E80,X
  stx $AB                    ; next call overwrites trailing $FF
  pla                        ; restore 1B caller $AA
  sta $AA
  jml $0CCF44

; ----------------------------------------------------------------------------
; Hook_F573: Stock ben_092..096 load + copy 2,048 B FontEn1bpp -> $7E:2000
; ----------------------------------------------------------------------------
Hook_F573:
  php
  phb
  rep #$30
  ldx #$0000
  ldy #$0000                 ; dst offset from $7E:2000
.dec_loop:
  phx
  phy
  lda.l $00F592,X            ; entry ID $5C..$60
  jsl $0AE20A                ; decompress into $7F:4000 (caller DBR preserved)
  rep #$30
  ply                        ; Y = dst offset from $7E:2000
  plx                        ; X = outer loop index (0..8)
  phx
  phb
  sep #$20
  lda #$7E
  pha
  plb
  rep #$20
  ; Copy $2000 bytes (except chunk 4: $0B00 bytes) from $7F:4000 -> $7E:2000,Y
  cpx #$0008
  beq .last_chunk
  lda #$2000
  bra .do_copy
.last_chunk:
  lda #$0B00
.do_copy:
  sta !VWF_TMP2
  ldx #$0000
.cp_font_blk:
  lda.l $7F4000,X
  sta $2000,Y
  iny
  iny
  inx
  inx
  cpx !VWF_TMP2
  bcc .cp_font_blk
  plb
  plx
  inx
  inx
  cpx #$000A
  bne .dec_loop

  ; Overwrite $7E:2000..$27FF (2,048 bytes = glyphs $00..$7F) with FontEn1bpp
  sep #$20
  lda #$7E
  pha
  plb
  rep #$20
  ldx #$0000
.cp_en:
  lda.l FontEn1bpp,X
  sta $2000,X
  inx
  inx
  cpx #$0800
  bcc .cp_en

  plb
  plp
  jml $00F591                ; RTS in bank $00

; ----------------------------------------------------------------------------
; Hook_F4D9: Render 5 proportional English default names -> $7E:A800..$A9DF (5 x 96 B)
; ----------------------------------------------------------------------------
Hook_F4D9:
  php
  phb
  rep #$30
  sep #$20
  lda #$7E
  pha
  plb
  rep #$20
  ; Clear $7E:A800..$A9DF (480 bytes)
  ldx #$0000
  lda #$0000
.clr:
  sta $A800,X
  inx
  inx
  cpx #$01E0
  bcc .clr

  ldx #$0000                 ; member offset (0, 2, 4, 6, 8)
.member_loop:
  phx
  txa
  ; dest_base = member * 96 = (m_idx * 32) * 3 ; since X = m_idx*2 -> (X << 4) * 3
  asl a
  asl a
  asl a
  asl a                      ; m_idx * 32
  sta !VWF_TMP
  asl a                      ; m_idx * 64
  clc
  adc !VWF_TMP               ; m_idx * 96
  sta !VWF_TMP2              ; dst_member_off ($0000..$0180)

  lda.l !PartyNames_Table,X  ; offset into bank $30 party name table
  tax                        ; X = index from !PartyNames_Table
  stz !VWF_PX                ; current px (0..47)

.char_loop:
  sep #$20
  lda.l !PartyNames_Table,X
  cmp #$FF
  bne +
  jmp .next_member
+
  inx
  phx                        ; save string index
  rep #$20
  and #$007F
  pha                        ; ch
  tax
  lda.l FontEnWidths,X
  and #$00FF
  sta !VWF_WIDTH
  lda !VWF_PX
  clc
  adc !VWF_WIDTH
  cmp #$0031                 ; clamp > 48px
  bcc .fits
  pla
  plx
  bra .next_member
.fits:
  pla                        ; ch
  asl a
  asl a
  asl a
  asl a
  sta !VWF_GLYPH             ; ch * 16

  ; Render 16 rows into tile0 = (px >> 3) and tile1 = tile0 + 1
  ldy #$0000                 ; row 0..15
.row_loop:
  sty !VWF_TMP               ; save row temporarily
  lda !VWF_GLYPH
  clc
  adc !VWF_TMP
  tax
  sep #$20
  lda.l FontEn1bpp,X         ; 8px row bits
  xba                        ; put in high byte of 16-bit shift reg (B:A = row:00)
  lda #$00
  rep #$20
  ; Shift 16-bit BA right by (px & 7) bits -> hi byte = tile0, lo byte = tile1!
  pha
  lda !VWF_PX
  and #$0007
  tax                        ; shift count 0..7
  pla
  cpx #$0000
  beq .no_sh
.sh_r:
  lsr a
  dex
  bne .sh_r
.no_sh:
  ; High byte = left tile, low byte = right tile
  pha                        ; shifted 16-bit value
  lda !VWF_PX
  and #$FFF8
  asl a                      ; (px >> 3) * 16 bytes
  clc
  adc !VWF_TMP2              ; + member * 96
  adc !VWF_TMP               ; + row
  tax                        ; dst offset in $7E:A800 (tile0, row)
  pla
  sep #$20
  pha                        ; keep low byte on stack
  xba                        ; A = high byte (left tile)
  ora $A800,X
  sta $A800,X
  pla                        ; A = low byte (right tile)
  beq .skip_r
  ora $A810,X
  sta $A810,X
.skip_r:
  rep #$20
  iny
  cpy #$0010
  bcc .row_loop

  lda !VWF_PX
  clc
  adc !VWF_WIDTH
  sta !VWF_PX
  plx
  jmp .char_loop

.next_member:
  rep #$20
  plx
  inx
  inx
  cpx #$000A
  bcs +
  jmp .member_loop
+

  plb
  plp
  jml $00F50A                ; RTS in bank $00

; ============================================================================
; VWF Buffer / Tile-Cache / Emitter Core (Caller guarantees DBR=$7E, M=0, X=0)
; ============================================================================
VwfClearBuf:
  stz !VWF_BUF
  stz !VWF_BUF+2
  stz !VWF_BUF+4
  stz !VWF_BUF+6
  stz !VWF_BUF+8
  stz !VWF_BUF+10
  stz !VWF_BUF+12
  stz !VWF_BUF+14
  rts

; Registers id in !VWF_TMP into active window ($AA) 4-stripe list, preserving X.
; Requires DBR=$7E, M=0, X=0.
VwfRegisterWinId:
  phx
  ldy $AA                    ; base WRAM addr of active window GC list ($D280/$D480/$D680/$D880)
  ldx #$0040                 ; 64 rows x 4 stripes = 256 words
.row:
  lda.w $0000,Y : bmi .s0 : cmp !VWF_TMP : beq .done
  lda.w $0080,Y : bmi .s1 : cmp !VWF_TMP : beq .done
  lda.w $0100,Y : bmi .s2 : cmp !VWF_TMP : beq .done
  lda.w $0180,Y : bmi .s3 : cmp !VWF_TMP : beq .done
  iny
  iny
  dex
  bne .row
  bra .done
.s0:
  lda !VWF_TMP : sta.w $0000,Y : bra .done
.s1:
  lda !VWF_TMP : sta.w $0080,Y : bra .done
.s2:
  lda !VWF_TMP : sta.w $0100,Y : bra .done
.s3:
  lda !VWF_TMP : sta.w $0180,Y
.done:
  plx
  rts

; Allocates or reuses a cached 8x16 tile matching !VWF_BUF.
; Returns A = BG3 VRAM tile index ($0030 if blank, or $0080 + slot_word_off).
VwfAllocTile:
  lda !VWF_BUF
  ora !VWF_BUF+2
  ora !VWF_BUF+4
  ora !VWF_BUF+6
  ora !VWF_BUF+8
  ora !VWF_BUF+10
  ora !VWF_BUF+12
  ora !VWF_BUF+14
  bne .non_blank
  lda #$0030
  rts

.non_blank:
  ; Compute 14-bit hash in $4000..$7FFF -> !VWF_TMP
  lda !VWF_BUF
  eor !VWF_BUF+2
  asl a
  eor !VWF_BUF+4
  asl a
  eor !VWF_BUF+6
  asl a
  eor !VWF_BUF+8
  asl a
  eor !VWF_BUF+10
  asl a
  eor !VWF_BUF+12
  asl a
  eor !VWF_BUF+14
  and #$3FFF
  ora #$4000
  sta !VWF_TMP

.probe_loop:
  ldx #$0000
  lda !VWF_TMP
.scan_cache:
  cmp $D000,X
  beq .check_ac
.scan_next:
  inx
  inx
  cpx #$0280
  bcc .scan_cache
  bra .alloc_new

.check_ac:
  txa
  asl a
  asl a
  asl a
  tay                        ; Y = X * 8 = slot byte offset in $7E:AC00
  lda $AC00,Y   : cmp !VWF_BUF    : bne .hash_bump
  lda $AC02,Y   : cmp !VWF_BUF+2  : bne .hash_bump
  lda $AC04,Y   : cmp !VWF_BUF+4  : bne .hash_bump
  lda $AC06,Y   : cmp !VWF_BUF+6  : bne .hash_bump
  lda $AC08,Y   : cmp !VWF_BUF+8  : bne .hash_bump
  lda $AC0A,Y   : cmp !VWF_BUF+10 : bne .hash_bump
  lda $AC0C,Y   : cmp !VWF_BUF+12 : bne .hash_bump
  lda $AC0E,Y   : cmp !VWF_BUF+14 : bne .hash_bump
  ; Cache HIT at slot X!
  phx
  jsr VwfRegisterWinId
  pla
  clc
  adc #$0080
  rts

.hash_bump:
  lda !VWF_TMP
  inc a
  and #$3FFF
  ora #$4000
  sta !VWF_TMP
  bra .probe_loop

.alloc_new:
  ldx #$0000
.find_free:
  lda $D000,X
  bmi .found_free
  inx
  inx
  cpx #$0280
  bcc .find_free
  ; Cache full fallback
  lda #$0030
  rts

.found_free:
  lda !VWF_TMP
  sta $D000,X
  phx
  jsr VwfRegisterWinId
  pla
  pha
  asl a
  asl a
  asl a
  tay
  lda !VWF_BUF    : sta $AC00,Y
  lda !VWF_BUF+2  : sta $AC02,Y
  lda !VWF_BUF+4  : sta $AC04,Y
  lda !VWF_BUF+6  : sta $AC06,Y
  lda !VWF_BUF+8  : sta $AC08,Y
  lda !VWF_BUF+10 : sta $AC0A,Y
  lda !VWF_BUF+12 : sta $AC0C,Y
  lda !VWF_BUF+14 : sta $AC0E,Y
  pla
  clc
  adc #$0080
  rts

; Appends raw 16-bit word in A to $1B80 + ($CD << 1) and increments $CD.
Append1B80Word:
  pha
  lda $CD
  asl a
  tax
  pla
  sta $1B80,X
  inc $CD
  rts

; Emits a newline ($FF00) or auto-page ($FF01) when $B2+1 == $D7 in $1B80 mode.
EmitPagedNewline:
  lda #$FF00
  ldx $B2
  inx
  cpx $D7
  bne .no_pg
  inc a                      ; $FF01
  ldx #$0000
.no_pg:
  stx $B2
  jsr Append1B80Word
  stz $B0
  rts

; Emits one drawable tile word (A < $FF00) to either $1A80 (!VWF_MODE=0) or $1B80 (=1).
VwfOutputTile:
  ldx !VWF_MODE
  bne .mode_paged
  pha
  lda $CD
  asl a
  tax
  pla
  sta $1A80,X
  inc $CD
  rts
.mode_paged:
  pha
  lda $B0
  cmp $D5
  bcc .no_wrap
  jsr EmitPagedNewline
.no_wrap:
  pla
  jsr Append1B80Word
  inc $B0
  rts

; Emits !VWF_BUF, clears buffer/dirty/px.
VwfEmitTile:
  jsr VwfAllocTile
  jsr VwfOutputTile
  jsr VwfClearBuf
  stz !VWF_PX
  stz !VWF_DIRTY
  rts

VwfFlush:
  lda !VWF_DIRTY
  beq .fl_done
  jsr VwfEmitTile
.fl_done:
  rts

; Fallback JSL wrapper to call stock $00:EA31 allocator (input: A = glyph_id)
JslStockEA31:
  phk
  pea .ret-1
  pea $EC62                  ; $00:EC63 is RTL (`6B`)!
  jml $00EA31
.ret:
  pha
  dec $CD
  pla
  rts

; Draws single 1bpp character ch ($00..$7F) in A into VWF stream.
; Requires DBR=$7E, M=0, X=0.
VwfDrawChar:
  pha                        ; ch
  tax
  lda.l FontEnWidths,X
  and #$00FF
  sta !VWF_WIDTH
  pla
  asl a
  asl a
  asl a
  asl a
  sta !VWF_GLYPH             ; glyph * 16

  ; OR glyph shifted right by !VWF_PX into !VWF_BUF (rows 0..15)
  ldy #$0000
  ldx !VWF_GLYPH
  lda !VWF_PX
  sta !VWF_TMP2              ; old_px
.r_loop:
  sep #$20
  lda.l FontEn1bpp,X
  phx
  ldx !VWF_TMP2
  beq .r_done_sh
.r_sh:
  lsr a
  dex
  bne .r_sh
.r_done_sh:
  ora !VWF_BUF,Y
  sta !VWF_BUF,Y
  plx
  rep #$20
  inx
  iny
  cpy #$0010
  bcc .r_loop

  lda #$0001
  sta !VWF_DIRTY
  lda !VWF_TMP2              ; old_px
  clc
  adc !VWF_WIDTH
  cmp #$0008
  bcc .fit_same
  ; Emits full tile, then writes spilled high bits at left edge (8 - old_px)
  sec
  sbc #$0008                 ; rem = old_px + width - 8
  pha                        ; save rem
  jsr VwfEmitTile            ; emits & clears !VWF_BUF, zeroes PX & DIRTY
  pla                        ; rem
  beq .done_dc               ; if rem == 0, clean!
  sta !VWF_PX
  lda #$0001
  sta !VWF_DIRTY
  lda #$0008
  sec
  sbc !VWF_TMP2              ; shift_l = 8 - old_px (1..7)
  sta !VWF_TMP               ; hold shift_l
  ldy #$0000
  ldx !VWF_GLYPH
.l_loop:
  sep #$20
  lda.l FontEn1bpp,X
  phx
  ldx !VWF_TMP
  beq .l_done_sh
.l_sh:
  asl a
  dex
  bne .l_sh
.l_done_sh:
  sta !VWF_BUF,Y             ; !VWF_BUF is freshly zeroed
  plx
  rep #$20
  inx
  iny
  cpy #$0010
  bcc .l_loop
  rts
.fit_same:
  sta !VWF_PX
.done_dc:
  rts

; Draws dynamically rendered party member name (member 0..4 in A) from $7E:A800 + m*96.
; Requires DBR=$7E, M=0, X=0.
VwfDrawPartyName:
  ; Compute base offset = A * 96 -> $06/$1E5E? Store in !VWF_GLYPH!
  asl a
  asl a
  asl a
  asl a
  asl a                      ; m * 32
  sta !VWF_GLYPH
  asl a                      ; m * 64
  clc
  adc !VWF_GLYPH             ; m * 96 (0, 96, 192, 288, 384)
  sta !VWF_GLYPH

  ; Scan 48 columns (0..47) to find first non-empty and last non-empty columns
  lda #$FFFF
  sta !VWF_TMP               ; first_col
  sta !VWF_TMP2              ; last_col
  ldy #$0000                 ; col 0..47
.scan_cols:
  tya
  and #$FFF8
  asl a                      ; (col >> 3) * 16
  clc
  adc !VWF_GLYPH
  tax                        ; X = base byte offset of this 8x16 column tile in $A800
  phy                        ; save col
  phx                        ; save $A800 tile offset
  tya
  and #$0007
  tax
  sep #$20
  lda.l BitMasks,X           ; $80 >> (col & 7)
  sta !VWF_WIDTH             ; single-byte mask in low byte
  plx                        ; restore $A800 tile offset
  lda #$00
  ldy #$0010                 ; 16 rows
.or_col:
  ora $A800,X
  inx
  dey
  bne .or_col
  and !VWF_WIDTH
  beq .empty_col
  rep #$20
  ply                        ; col
  lda !VWF_TMP
  cmp #$FFFF
  bne .set_last
  sty !VWF_TMP
.set_last:
  sty !VWF_TMP2
  bra .next_scan
.empty_col:
  rep #$20
  ply
.next_scan:
  iny
  cpy #$0030
  bcc .scan_cols

  lda !VWF_TMP
  cmp #$FFFF
  bne .has_pixels
  lda #$0020                 ; fallback space if blank
  jmp VwfDrawChar

.has_pixels:
  ; Blit col = first_col .. last_col into !VWF_BUF
  ldy !VWF_TMP
.blit_col:
  phy                        ; 1,S = cur col
  tya
  and #$0007
  tax
  sep #$20
  lda.l BitMasks,X
  sta !VWF_WIDTH+1           ; high byte = src_mask
  rep #$20
  lda !VWF_PX
  tax
  sep #$20
  lda.l BitMasks,X
  sta !VWF_WIDTH             ; low byte = dst_mask ($80 >> px)
  rep #$20
  lda 1,S
  and #$FFF8
  asl a
  clc
  adc !VWF_GLYPH
  tay                        ; Y = src base in $A800
  ldx #$0000                 ; row 0..15
  sep #$20
.blit_row:
  lda $A800,Y
  and !VWF_WIDTH+1           ; src_mask
  beq .no_px_bit
  lda !VWF_BUF,X
  ora !VWF_WIDTH             ; dst_mask
  sta !VWF_BUF,X
.no_px_bit:
  iny
  inx
  cpx #$0010
  bcc .blit_row

  rep #$20
  lda #$0001
  sta !VWF_DIRTY
  inc !VWF_PX
  lda !VWF_PX
  cmp #$0008
  bcc .no_emit_col
  jsr VwfEmitTile
.no_emit_col:
  ply                        ; cur col
  cpy !VWF_TMP2
  beq .after_cols
  iny
  bra .blit_col

.after_cols:
  ; 1px kerning advance after name
  lda #$0001
  sta !VWF_DIRTY
  inc !VWF_PX
  lda !VWF_PX
  cmp #$0008
  bcc .done_pn
  jsr VwfEmitTile
.done_pn:
  rts

BitMasks:
  db $80, $40, $20, $10, $08, $04, $02, $01

; Shared handler for single-byte chars < $F0 (VWF / static $00..$1F / katakana fallback)
VwfHandleSingleByte:
  cmp #$0010
  bne .not_pad
  jsr VwfFlush
  lda #$0030
  jmp VwfOutputTile
.not_pad:
  cmp #$0020
  bcs .not_static
  ldx !VWF_PX
  bne .use_vwf               ; inside a VWF tile -> draw via VwfDrawChar
  asl a
  tax
  lda.l $00EA40,X            ; static VRAM tile $0010..$004E (zero cache cost!)
  jmp VwfOutputTile
.not_static:
  cmp #$0080
  bcc .use_vwf
  pha
  jsr VwfFlush
  pla
  jsr JslStockEA31
  jmp VwfOutputTile
.use_vwf:
  jmp VwfDrawChar

; Shared handler for 2-byte $F0..$F7 tokens (party names $F440..$F44E or kanji fallback)
VwfHandleTwoByte:
  xba
  and #$FF00
  sta !VWF_TMP
  ldy !VWF_STR_Y
  lda [$A0],Y
  iny
  sty !VWF_STR_Y
  and #$00FF
  ora !VWF_TMP               ; w = (b0<<8) | b1
  pha
  and #$FF00
  cmp #$F400
  bne .kanji_fb
  pla
  pha
  and #$00FF
  sec
  sbc #$0040
  bcc .kanji_fb
  cmp #$000D                 ; 0..12
  bcs .kanji_fb
  ldy #$0000
.chk_m3:
  cmp #$0000
  beq .is_m3
  sec
  sbc #$0003
  bmi .kanji_fb
  iny
  bra .chk_m3
.is_m3:
  pla
  pha
  clc
  adc #$0001
  xba                        ; ((b1+1)<<8) | $F4
  ldy !VWF_STR_Y
  cmp [$A0],Y
  bne .kanji_fb
  lda !VWF_STR_Y
  clc
  adc #$0004
  sta !VWF_STR_Y
  pla
  and #$00FF
  sec
  sbc #$0040
  ldy #$0000
.div3:
  cmp #$0003
  bcc .got_m
  sec
  sbc #$0003
  iny
  bra .div3
.got_m:
  tya
  jmp VwfDrawPartyName
.kanji_fb:
  jsr VwfFlush
  pla
  and #$07FF
  asl a
  pha
  jsr JslStockEA31
  jsr VwfOutputTile
  pla
  inc a
  jsr JslStockEA31
  jmp VwfOutputTile

; ============================================================================
; Hook_E9A3: Direct string VWF engine ($1A80, exits via JML $00E9CE)
; ============================================================================
Hook_E9A3:
  stz !VWF_PX
  stz !VWF_DIRTY
  stz !VWF_MODE
  jsr VwfClearBuf
  sty !VWF_STR_Y             ; initial Y = 0
.loop:
  ldy !VWF_STR_Y
  lda [$A0],Y
  iny
  sty !VWF_STR_Y
  and #$00FF
  cmp #$00F0
  bcc .single
  cmp #$00F8
  bcc .two_byte
  cmp #$00FB
  beq .vwf_sep
  cmp #$00FC
  bcc .exit_rts              ; $F8..$FA -> stock E9B3/E9CD RTS
  beq .ctrl_fc
  cmp #$00FF
  bne .loop                  ; $FD/$FE skipped in immediate print
  jsr VwfFlush
  lda $CD
  asl a
  tax
  lda #$FFFF
  sta $1A80,X
  inc $CD
.exit_rts:
  jml $00E9CE

.vwf_sep:
  jsr VwfFlush
  jmp .loop

.ctrl_fc:
  jsr VwfFlush
  ldy !VWF_STR_Y
  lda [$A0],Y
  iny
  and #$00FF
  bne .fc_nz
  lda #$FF02
  bra .fc_1w
.fc_nz:
  dec a
  bne .fc_n1
  lda #$FF03
.fc_1w:
  sty !VWF_STR_Y
  jsr VwfOutputTile
  bra .loop
.fc_n1:
  dec a
  bne .fc_n2
  lda #$FF04
  bra .fc_2w
.fc_n2:
  lda #$FF05
.fc_2w:
  jsr VwfOutputTile
  lda [$A0],Y
  iny
  sty !VWF_STR_Y
  and #$00FF
  jsr VwfOutputTile
  jmp .loop

.single:
  jsr VwfHandleSingleByte
  jmp .loop
.two_byte:
  jsr VwfHandleTwoByte
  jmp .loop

; ============================================================================
; Hook_ED80: Paged dialogue VWF engine ($1B80, enters M=1 X=0, exits -> $00EE42)
; ============================================================================
Hook_ED80:
  sta.l $001959              ; displaced from $00:ED80 (while M=1)
  rep #$30
  stz $B2
  stz $B0
  stz !VWF_PX
  stz !VWF_DIRTY
  lda #$0001
  sta !VWF_MODE
  jsr VwfClearBuf
  stz !VWF_STR_Y
.loop:
  ldy !VWF_STR_Y
  lda [$A0],Y
  iny
  sty !VWF_STR_Y
  and #$00FF
  cmp #$00F0
  bcs +
  jmp .single
+
  cmp #$00F8
  bcs +
  jmp .two_byte
+
  cmp #$00FC
  bcc .loop                  ; $F8..$FB -> stock no-op
  beq .ctrl_fc
  cmp #$00FD
  beq .ctrl_fd
  cmp #$00FE
  beq .ctrl_fe
  ; $FF ({end}) - match stock $00:EE25..EE42 trailing line fill
  jsr VwfFlush
.end_pad:
  inc $B2
  lda $B2
  cmp $D7
  bcs .end_term
  lda #$FF00
  jsr Append1B80Word
  bra .end_pad
.end_term:
  lda #$FFFF
  jsr Append1B80Word
  jml $00EE42                ; JSR $EC64 -> JSR $EED3 in bank $00

.ctrl_fd:                    ; {nl}
  jsr VwfFlush
  jsr EmitPagedNewline
  jmp .loop

.ctrl_fe:                    ; {page} - match stock $00:EDE3 line-fill + $FF01
  jsr VwfFlush
.pg_pad:
  lda #$FF00
  jsr Append1B80Word
  inc $B2
  lda $B2
  cmp $D7
  bcc .pg_pad
  lda $CD
  asl a
  tax
  lda #$FF01
  sta $1B7E,X
  stz $B2
  stz $B0
  jmp .loop

.ctrl_fc:
  jsr VwfFlush
  ldy !VWF_STR_Y
  lda [$A0],Y
  iny
  and #$00FF
  bne .fc_nz
  lda #$FF02
  bra .fc_1w
.fc_nz:
  dec a
  bne .fc_n1
  lda #$FF03
.fc_1w:
  sty !VWF_STR_Y
  jsr Append1B80Word
  jmp .loop
.fc_n1:
  dec a
  bne .fc_n2
  lda #$FF04
  bra .fc_2w
.fc_n2:
  lda #$FF05
.fc_2w:
  jsr Append1B80Word
  lda [$A0],Y
  iny
  sty !VWF_STR_Y
  and #$00FF
  jsr Append1B80Word
  jmp .loop

.single:
  jsr VwfHandleSingleByte
  jmp .loop
.two_byte:
  jsr VwfHandleTwoByte
  jmp .loop

; ============================================================================
; Hook_01A2A2: Name Entry confirm ($01:A2A2) proportional renderer -> [$00]
; Entry: DP $00/$02 = $7E:A800+slot*96, M=0, X=0. Exits via JML $01A303.
; ============================================================================
Hook_01A2A2:
  php
  phb
  rep #$30
  sep #$20
  lda #$7E
  pha
  plb                        ; DB = $7E for !VWF_*
  rep #$20

  ldy #$0000
  lda #$0000
.clr:
  sta [$00],Y
  iny
  iny
  cpy #$0060
  bcc .clr

  lda.l $7EFA11              ; typed length (0..6)
  and #$00FF
  cmp #$0007
  bcc .len_ok
  lda #$0006
.len_ok:
  sta !VWF_DIRTY
  stz !VWF_STR_Y
  stz !VWF_PX

.char_loop:
  lda !VWF_STR_Y
  cmp !VWF_DIRTY
  bcc +
  jmp .done
+
  tax
  inc !VWF_STR_Y
  lda.l $7EFA0B,X
  and #$00FF
  cmp #$00F0
  bcc +
  jmp .two_byte
+
  cmp #$0080
  bcs .char_loop
  cmp #$0010                 ; {pad} inside typed name -> space advance
  bne .not_pad
  lda #$0020
.not_pad:
  pha                        ; ch (0..$7F)
  tax
  lda.l FontEnWidths,X
  and #$00FF
  sta !VWF_WIDTH
  lda !VWF_PX
  clc
  adc !VWF_WIDTH
  cmp #$0031                 ; clamp <= 48px (6 tiles)
  bcc .fits
  pla
  jmp .done
.fits:
  pla
  asl a
  asl a
  asl a
  asl a
  sta !VWF_GLYPH             ; ch * 16
  lda !VWF_PX
  and #$FFF8
  asl a
  sta !VWF_TMP2              ; tile0 * 16
  stz !VWF_TMP               ; row 0..15

.row_loop:
  lda !VWF_GLYPH
  clc
  adc !VWF_TMP
  tax
  sep #$20
  lda.l FontEn1bpp,X
  xba
  lda #$00
  rep #$20                   ; BA = row:00
  pha
  lda !VWF_PX
  and #$0007
  tax
  pla
  cpx #$0000
  beq .no_sh
.sh_r:
  lsr a
  dex
  bne .sh_r
.no_sh:
  pha                        ; shifted 16-bit value (hi=left, lo=right)
  lda !VWF_TMP2
  clc
  adc !VWF_TMP
  tay
  pla
  sep #$20
  pha                        ; keep low byte on stack (1 byte)
  xba                        ; high byte -> left tile
  ora [$00],Y
  sta [$00],Y
  pla                        ; low byte -> right tile
  beq .skip_r
  cpy #$0050                 ; guard tile1 <= tile5 (< 96 bytes)
  bcs .skip_r
  xba
  rep #$20
  tya
  clc
  adc #$0010
  tay
  sep #$20
  xba
  ora [$00],Y
  sta [$00],Y
.skip_r:
  rep #$20
  inc !VWF_TMP
  lda !VWF_TMP
  cmp #$0010
  bcc .row_loop

  lda !VWF_PX
  clc
  adc !VWF_WIDTH
  sta !VWF_PX
  jmp .char_loop

.two_byte:
  ; $F0..$FF 2-byte glyph (e.g. custom kanji) from $7E:2000, aligned to 8px tile
  ldx !VWF_STR_Y
  cpx !VWF_DIRTY
  bcs .done
  inc !VWF_STR_Y
  and #$000F
  xba
  sep #$20
  lda.l $7EFA0B,X
  rep #$20
  asl a
  asl a
  asl a
  asl a
  asl a
  tax                        ; X = ((b0 & $0F) << 8 | b1) * 32
  lda !VWF_PX
  clc
  adc #$0007
  and #$FFF8
  sta !VWF_PX
  cmp #$0021                 ; need 16px (px <= 32)
  bcs .done
  asl a
  tay
  lda #$0010                 ; 16 words (32 bytes = 2 tiles)
  sta !VWF_TMP
.k_copy:
  lda.l $7E2000,X
  sta [$00],Y
  inx
  inx
  iny
  iny
  dec !VWF_TMP
  bne .k_copy
  lda !VWF_PX
  clc
  adc #$0010
  sta !VWF_PX
  jmp .char_loop

.done:
  plb
  plp
  jml $01A303

assert pc() <= $30A000

; ============================================================================
; Bank $30:A000..$30:A8FF - Static 1bpp English Font & Advance Widths
; ============================================================================
org $30A000
FontEn1bpp:
  incbin "font_en_1bpp.bin"

org $30A800
FontEnWidths:
  incbin "font_en_widths.bin"

assert pc() <= $30A900
