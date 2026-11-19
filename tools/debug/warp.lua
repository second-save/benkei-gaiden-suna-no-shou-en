-- Cold-boot debug warp harness for Benkei Gaiden: Suna no Shou (SNES / MesenCE 2.2.1).
-- Usage via tools/run_emu.py:
--   --script tools/debug/warp.lua --var "SCENE='<name>'" [--var "GOD=1"] [--var "NOENC=1"] [--var "FAST=1"]

if not SCENES then
  local src = (debug.getinfo(1, "S").source or ""):gsub("^@", "")
  local candidates = {}
  if SCENE_FILE then candidates[#candidates + 1] = SCENE_FILE end
  for _, p in ipairs({ OUT or "", STATE_OUT or "", src }) do
    local root = p:match("^(.-)[/\\]work[/\\]") or p:match("^(.-)[/\\]build[/\\]")
    if root and root ~= "" then
      candidates[#candidates + 1] = root .. "/tools/debug/scenes.lua"
    end
  end
  local sdir = src:match("^(.*[/\\])") or ""
  candidates[#candidates + 1] = sdir .. "scenes.lua"
  candidates[#candidates + 1] = "tools/debug/scenes.lua"
  candidates[#candidates + 1] = "../../../../tools/debug/scenes.lua"
  candidates[#candidates + 1] = "../../../debug/scenes.lua"
  candidates[#candidates + 1] = "../../debug/scenes.lua"
  candidates[#candidates + 1] = "../debug/scenes.lua"
  local loaded = false
  for _, path in ipairs(candidates) do
    local f = io.open(path, "rb")
    if f then
      f:close()
      dofile(path)
      loaded = true
      break
    end
  end
  if not loaded or not SCENES then
    L.fail("warp.lua: could not load tools/debug/scenes.lua")
    return
  end
end

if not SCENE or SCENE == "" or not SCENES[SCENE] then
  local names = {}
  for k, _ in pairs(SCENES or {}) do names[#names + 1] = k end
  table.sort(names)
  L.fail("warp.lua: invalid SCENE=" .. tostring(SCENE) .. " (valid: " .. table.concat(names, ", ") .. ")")
  return
end

local cfg = SCENES[SCENE]
local stage = 0
local warp_done = false
local logged_ok = false

local function wmem(addr, val)
  emu.write(addr, val & 0xFF, emu.memType.snesWorkRam)
end

local function wmem16(addr, val)
  wmem(addr, val & 0xFF)
  wmem(addr + 1, (val >> 8) & 0xFF)
end

local function rmem(addr)
  return emu.read(addr, emu.memType.snesWorkRam)
end

local function rmem16(addr)
  return rmem(addr) | (rmem(addr + 1) << 8)
end

local function apply_flags_and_mods()
  if cfg.flags then
    for addr, val in pairs(cfg.flags) do
      wmem(addr, val)
    end
  end
  if NOENC and NOENC ~= 0 and NOENC ~= false then
    -- Flag $03 -> $0D00 bit 4 ($10) disables field random encounters ($01:842E)
    wmem(0x0D00, rmem(0x0D00) | 0x10)
  end
  if FAST and FAST ~= 0 and FAST ~= false then
    -- High gold + buffed Lv10 stats for quick QA
    wmem(0x0D2A, 0x50)
    wmem(0x0D2B, 0xC3)
    wmem(0x0D2C, 0x00) -- 50,000 ryo
    wmem16(0x1082, 400) -- HP
    wmem16(0x1084, 100) -- MP
    wmem(0x108A, 15)    -- Lv 15
    wmem16(0x1090, 80)  -- ATK
    wmem16(0x1092, 60)  -- STR
    wmem16(0x1094, 40)  -- AGI
  end
end

-- Stage 1: Skip Sunsoft splash ($00:805A -> $00:805E)
L.on_exec(0x00805A, 0x00805A, function()
  if stage < 1 then
    stage = 1
    local s = emu.getState()
    s["cpu.pc"] = 0x805E
    emu.setState(s)
  end
end)

-- Stage 2: Optionally skip Title logo fade-in animation ($00:8064 -> $00:8086)
L.on_exec(0x008064, 0x008064, function()
  if cfg.mode == "title" and not cfg.skip_title_anim then
    return
  end
  if stage < 2 then
    stage = 2
    local s = emu.getState()
    s["cpu.pc"] = 0x8086
    emu.setState(s)
  end
end)

-- Stage 3: For non-title scenes, skip Title menu straight into NewGameInit ($00:8090 -> $00:80BE)
L.on_exec(0x008090, 0x008090, function()
  if cfg.mode == "title" then
    if not logged_ok then
      logged_ok = true
      L.log("WARP_OK " .. SCENE)
    end
    return
  end
  if stage < 3 then
    stage = 3
    local s = emu.getState()
    s["cpu.pc"] = 0x80BE
    emu.setState(s)
  end
end)

-- Stage 4: Handle name_entry vs skipping Name Entry ($00:87D7 -> $00:88B4)
L.on_exec(0x0087D7, 0x0087D7, function()
  if cfg.mode == "name_entry" then
    stage = math.max(stage, 4)
    return -- Let natural Name Entry (Gender -> Rename prompt -> Kana Grid) run
  end
  if stage < 4 then
    stage = 4
    local s = emu.getState()
    s["cpu.pc"] = 0x88B4 -- Skip past $01:ACE4 into WRAM init
    emu.setState(s)
  end
end)

-- Stage 5: Override map, coords, flags, and mods right before JSR $9348 LoadMap ($00:8922)
L.on_exec(0x008922, 0x008922, function()
  if cfg.mode == "name_entry" or cfg.mode == "title" then
    return
  end
  if stage < 5 then
    stage = 5
    if cfg.map then
      wmem(0x0052, cfg.map & 0xFF)
      wmem(0x0053, (cfg.map >> 8) & 0xFF)
      wmem(0x0054, cfg.x or 0x10)
      wmem(0x0055, cfg.y or 0x10)
      wmem(0x006C, cfg.dir or 0xFF)
      wmem(0x006D, cfg.flg or 0xBE)
    end
    apply_flags_and_mods()
  end
end)

-- Stage 6: Skip opening cutscene ($00:8925 -> $00:8928 RTS)
L.on_exec(0x008925, 0x008925, function()
  if cfg.mode == "name_entry" or cfg.mode == "title" then
    return
  end
  if stage < 6 then
    stage = 6
    local s = emu.getState()
    s["cpu.pc"] = 0x8928
    emu.setState(s)
    if cfg.mode == "map" then
      warp_done = true
    end
  end
end)

-- Stage 7 (battle / jump): Hook FieldLoop's JSL $01:8429 entry ($01:8429, RTL to FieldLoop already on stack)
L.on_exec(0x018429, 0x018429, function()
  if stage < 6 or warp_done then return end
  if cfg.mode == "battle" then
    warp_done = true
    apply_flags_and_mods()
    wmem(0x1A03, cfg.boss_flag or 0x00)
    local s = emu.getState()
    s["cpu.k"] = 0x00
    s["cpu.pc"] = 0x84A2
    s["cpu.x"] = cfg.battle_group or 0x002E
    s["cpu.y"] = cfg.battle_bg or 0x001E
    s["cpu.ps"] = s["cpu.ps"] & 0xFFEF -- Ensure 16-bit X/Y for EnterBattle ($00:84A2)
    emu.setState(s)
    L.log(string.format("battle warp -> group=$%04X bg=$%04X boss=$%02X",
      cfg.battle_group or 0x002E, cfg.battle_bg or 0x001E, cfg.boss_flag or 0))
  elseif cfg.mode == "jump" then
    warp_done = true
    apply_flags_and_mods()
    local s = emu.getState()
    s["cpu.k"] = cfg.jump_k
    s["cpu.pc"] = cfg.jump_pc
    if cfg.jump_dbr then s["cpu.dbr"] = cfg.jump_dbr end
    if cfg.jump_ps then s["cpu.ps"] = cfg.jump_ps end
    emu.setState(s)
    L.log(string.format("jump warp -> $%02X:%04X", cfg.jump_k, cfg.jump_pc))
  end
end)

-- Optional mid-scene skip hook (e.g. chapter_card $03:D374 -> $03:D41D after ben_097 load)
if cfg and cfg.jump_skip_from and cfg.jump_skip_to then
  local skipped_sub = false
  L.on_exec(cfg.jump_skip_from, cfg.jump_skip_from, function()
    if warp_done and not skipped_sub then
      skipped_sub = true
      local s = emu.getState()
      s["cpu.pc"] = cfg.jump_skip_to
      emu.setState(s)
      L.log(string.format("jump sub-skip -> $%02X:%04X", cfg.jump_k, cfg.jump_skip_to))
    end
  end)
end

-- Per-frame verification and GOD/NOENC pinning
L.on_frame(function(n)
  if GOD and GOD ~= 0 and GOD ~= false then
    for slot = 0, 5 do
      local base = 0x1080 + slot * 0x20
      if rmem16(base) ~= 0xFFFF then
        if rmem16(base + 2) < 200 then wmem16(base + 2, 200) end
        if rmem16(base + 4) < 50 then wmem16(base + 4, 50) end
      end
    end
  end
  if NOENC and NOENC ~= 0 and NOENC ~= false and stage >= 5 then
    wmem(0x0D00, rmem(0x0D00) | 0x10)
  end

  if logged_ok then return end

  if cfg.mode == "name_entry" and stage >= 4 and n >= 120 then
    logged_ok = true
    L.log("WARP_OK " .. SCENE)
  elseif cfg.mode == "map" and stage >= 6 and rmem16(0x0D28) == cfg.expect_map then
    logged_ok = true
    L.log(string.format("WARP_OK %s map=$%04X x=$%02X y=$%02X", SCENE, rmem16(0x0D28), rmem(0x0D89), rmem(0x0D8B)))
  elseif cfg.mode == "battle" and warp_done and rmem(0x1380) == 0xFF then
    logged_ok = true
    L.log(string.format("WARP_OK %s b1380=$FF", SCENE))
  elseif cfg.mode == "jump" and warp_done and (rmem(0x76) & 0x80) == 0 and (rmem(0x76) & 0x0F) > 0 and n >= math.floor((cfg.frames or 360) * 0.75) then
    logged_ok = true
    L.log(string.format("WARP_OK %s frame=%d", SCENE, n))
  end
end)
