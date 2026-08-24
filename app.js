/**
 * ZENLESS ZONE ZERO COMBAT SETTLEMENT ENGINE & CALCULATOR
 * Premium Glassmorphism Front-End Controller
 * Developed with absolute precision and premium aesthetics
 */

// =====================================================================
// 1. CONSTANTS & SYSTEM CURVES
// =====================================================================
const HP_CURVE = [100, 116, 136, 159, 183, 200, 219, 240, 263, 303, 326, 352, 379, 409, 471, 485, 499, 514, 530, 610, 685, 770, 865, 973, 1119, 1132, 1146, 1160, 1174, 1351, 1411, 1475, 1541, 1611, 1853, 1858, 1864, 1870, 1876, 2158, 2228, 2302, 2377, 2455, 2824, 2847, 2872, 2896, 2920, 3213, 3293, 3376, 3460, 3547, 4080, 4106, 4132, 4158, 4185, 4604, 4637, 4671, 4705, 4739, 4774, 4809, 4844, 4879, 4915, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406, 5406];
const ATTACK_CURVE = [100, 116, 133, 150, 167, 183, 199, 213, 227, 242, 265, 289, 312, 336, 359, 383, 406, 430, 453, 477, 496, 515, 534, 553, 573, 592, 611, 630, 649, 669, 685, 701, 717, 734, 750, 766, 783, 799, 815, 832, 846, 860, 875, 889, 904, 918, 932, 947, 961, 976, 982, 995, 1002, 1009, 1015, 1022, 1029, 1035, 1042, 1049, 1055, 1062, 1069, 1075, 1082, 1089, 1095, 1102, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109, 1109];
const DEFENCE_CURVE = [100, 108, 116, 124, 132, 142, 152, 164, 176, 188, 200, 214, 228, 242, 258, 274, 290, 306, 324, 344, 362, 382, 402, 422, 444, 466, 490, 512, 536, 562, 586, 612, 638, 666, 694, 722, 750, 780, 810, 842, 872, 904, 938, 970, 1004, 1038, 1074, 1110, 1146, 1184, 1220, 1258, 1298, 1338, 1378, 1418, 1460, 1502, 1544, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588];
const STUN_CURVE = [100, 100, 100, 100, 103, 103, 103, 103, 103, 103, 103, 104, 104, 105, 106, 106, 107, 107, 108, 109, 110, 111, 113, 114, 116, 117, 118, 120, 121, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 134, 135, 136, 137, 139, 140, 141, 143, 144, 145, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167, 167];

const S_SUBSTAT_VALUES = {
    "atk_pct": 3.0,          // 3.0%
    "crit_rate": 2.4,        // 2.4%
    "crit_dmg": 4.8,         // 4.8%
    "hp_pct": 3.0,           // 3.0%
    "def_pct": 4.8,          // 4.8%
    "atk_flat": 19,          // +19
    "def_flat": 15,          // +15
    "hp_flat": 112,          // +112
    "pen_flat": 9,           // +9
    "anomaly_prof": 9        // +9
};

const SUBSTAT_LABELS = {
    "none": "无 sub-stat",
    "atk_pct": "攻击力百分比 (+3.0%)",
    "crit_rate": "暴击率 (+2.4%)",
    "crit_dmg": "暴击伤害 (+4.8%)",
    "hp_pct": "生命值百分比 (+3.0%)",
    "def_pct": "防御力百分比 (+4.8%)",
    "atk_flat": "攻击力固定值 (+19)",
    "def_flat": "防御力固定值 (+15)",
    "hp_flat": "生命值固定值 (+112)",
    "pen_flat": "穿透值固定值 (+9)",
    "anomaly_prof": "异常精通固定值 (+9)"
};

// =====================================================================
// 2. GLOBAL DATABASE STATE
// =====================================================================
let DB = {
    characters: {},
    weapons: {},
    driveDiscs: {},
    monsters: {},
    crisisBuffs: {}
};

// 2.5 CHARACTERS STATIC & DYNAMIC BUFFS CONFIGURATION
// =====================================================================
// CHAR_BUFFS_CONFIG is now successfully loaded externally from dict/extracted_all_buffs.js


let activeBuffsState = {}; // Toggled buff ID states

// Reactivity State
let squad = [null, null, null]; // 1-3 Active characters
// 米游社标准化账号导入后的完整角色构筑。它只用于把账号角色放入小队，
// 不参与规则判断，也不替代静态角色/音擎/驱动盘数据库。
let importedAccountBuilds = [];
let activeSlotIndex = 0;        // Currently active builder slot
let targetMonsterId = "";
let targetMonsterLevel = 70;    // Level slider (1-80)
let stunnedState = false;
let selectedCrisisBuffs = new Set();
let activeSkillCategory = "basic";
let activeSkillLevel = "lv12";

// 计算后端桥接：界面仍由本文件和原有 index.css 负责；新版公式只作为
// 结算实现加载，不复制到前端，也不改变旧版页面结构。
globalThis.ZZZ_NEW_ENGINE_READY = import("./dist/src/web/engine-entry.js?rules-20260815-18")
    .then((engine) => {
        globalThis.ZZZ_NEW_ENGINE = engine;
        return engine;
    })
    .catch((error) => {
        console.warn("新版计算引擎桥接加载失败，将回退到旧版公式：", error);
        return null;
    });

// =====================================================================
// 3. LIFECYCLE & ASSET LOADERS
// =====================================================================
document.addEventListener("DOMContentLoaded", async () => {
    try {
        // 等待新版计算核心桥接完成；若页面以 file:// 打开或 dist 尚未生成，
        // 桥接层会返回 null，旧版界面和旧公式仍可继续工作。
        await (globalThis.ZZZ_NEW_ENGINE_READY || Promise.resolve(null));
        if (globalThis.ZZZ_NEW_ENGINE) {
            console.log("新版计算引擎已接入：", globalThis.ZZZ_NEW_ENGINE.getWebEngineStatus());
        }
        await loadDatabases();
        initDefaultRoster();
        initEventBindings();
        updateUI();
    } catch (err) {
        console.error("Initialization Failed:", err);
        const pool = document.getElementById("character-grid-pool");
        if (pool) pool.innerHTML = `<div class="text-red p-4">数据库加载失败，请通过 local server 模式运行。详细错误：${err.message}</div>`;
    }
});

function fixWeaponSecondaryStats() {
    const reference = {
        "暴击率": 24.0,
        "暴击伤害": 48.0,
        "攻击力百分比": 30.0,
        "穿透率": 24.0,
        "异常精通": 92.0,
        "能量自动回复": 60.0,
        "生命值百分比": 30.0,
        "防御力百分比": 40.0,
        "冲击力": 18.0,
        "异常掌控": 30.0
    };
    
    for (let wid in DB.weapons) {
        const weapon = DB.weapons[wid];
        const sec = weapon.stats_lv60_star5 && weapon.stats_lv60_star5.secondary_stat;
        if (!sec) continue;
        
        let mult = 1.0;
        if (weapon.rarity === "A") {
            mult = 5.0 / 6.0;
        } else if (weapon.rarity === "B") {
            mult = 4.0 / 6.0;
        }
        
        const name2 = sec.name2;
        if (reference[name2] !== undefined) {
            const baseVal = reference[name2];
            sec.value = parseFloat((baseVal * mult).toFixed(2));
        }
    }
}

async function loadDatabases() {
    // Check if data is already loaded globally via <script> tags to bypass local file:// CORS restrictions
    if (window.ZZZ_CHARACTERS && window.ZZZ_WEAPONS && window.ZZZ_DRIVE_DISCS && window.ZZZ_MONSTERS && window.ZZZ_CRISIS_BUFFS) {
        DB.characters = window.ZZZ_CHARACTERS;
        DB.weapons = window.ZZZ_WEAPONS;
        DB.driveDiscs = window.ZZZ_DRIVE_DISCS;
        DB.monsters = window.ZZZ_MONSTERS;
        DB.crisisBuffs = window.ZZZ_CRISIS_BUFFS;
        console.log("Databases loaded offline via global variables successfully!");
        fixWeaponSecondaryStats();
        return;
    }

    // HTTP Server Fallback (Fetch JSON files)
    const urls = {
        characters: "dict/zzz_characters.json",
        weapons: "dict/zzz_weapons.json",
        driveDiscs: "dict/zzz_drive_discs.json",
        monsters: "dict/zzz_monsters.json",
        crisisBuffs: "dict/zzz_crisis_buffs.json"
    };

    const fetchJson = async (url) => {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP error ${res.status} fetching ${url}`);
        return res.json();
    };

    const [chars, weaps, discs, mons, buffs] = await Promise.all([
        fetchJson(urls.characters),
        fetchJson(urls.weapons),
        fetchJson(urls.driveDiscs),
        fetchJson(urls.monsters),
        fetchJson(urls.crisisBuffs)
    ]);

    DB.characters = chars;
    DB.weapons = weaps;
    DB.driveDiscs = discs;
    DB.monsters = mons;
    DB.crisisBuffs = buffs;
    
    console.log("Databases populated via fetch successfully:", Object.keys(DB).map(k => `${k}: ${Object.keys(DB[k]).length || (DB[k].sets ? Object.keys(DB[k].sets).length : 0)}`));
    fixWeaponSecondaryStats();
}

function initDefaultRoster() {
    // Populate character roster grid
    const rosterPool = document.getElementById("character-grid-pool");
    if (!rosterPool) return;
    
    rosterPool.innerHTML = "";
    Object.values(DB.characters).forEach(char => {
        const card = document.createElement("div");
        card.className = `char-pool-card rarity-${char.rarity}`;
        card.draggable = true;
        card.dataset.id = char.id;
        
        card.innerHTML = `
            <span class="char-element-badge">${getElementEmoji(char.element)}</span>
            <img src="${char.icon_path || 'asset/character/Unknown.webp'}" class="char-pool-avatar" alt="${char.name}">
            <div class="char-pool-name text-xs">${char.name}</div>
        `;
        
        // Drag events
        card.addEventListener("dragstart", (e) => {
            e.dataTransfer.setData("text/plain", char.id);
            e.dataTransfer.effectAllowed = "copyMove";
        });

        // Click-to-equip fallback
        card.addEventListener("click", () => {
            equipCharacterToFirstAvailable(char.id);
        });

        rosterPool.appendChild(card);
    });

    // Populate Monster selector dropdown
    const monsterDropdown = document.getElementById("select-target-boss");
    if (monsterDropdown) {
        monsterDropdown.innerHTML = "";
        
        // Prioritize Bosses (rarity >= 1)
        const sortedMonsters = Object.values(DB.monsters).sort((a, b) => (b.rarity || 0) - (a.rarity || 0));
        sortedMonsters.forEach(m => {
            const opt = document.createElement("option");
            opt.value = m.id;
            opt.textContent = `${m.rarity >= 1 ? '👑 ' : '👾 '}${m.name} (${m.code_name.replace("Monster_", "")})`;
            monsterDropdown.appendChild(opt);
        });
        
        if (sortedMonsters.length > 0) {
            targetMonsterId = sortedMonsters[0].id;
            monsterDropdown.value = targetMonsterId;
        }
    }

    // Populate Drive Disc Set Roster (in Tab C)
    const setGridPool = document.getElementById("drive-set-grid-pool");
    if (setGridPool && DB.driveDiscs.sets) {
        setGridPool.innerHTML = "";
        Object.values(DB.driveDiscs.sets).forEach(set => {
            const setCard = document.createElement("div");
            setCard.className = "char-pool-card rarity-A";
            setCard.style.flex = "0 0 86px";
            setCard.style.height = "86px";
            setCard.draggable = true;
            setCard.dataset.setId = set.id;
            
            setCard.innerHTML = `
                <img src="${set.icon_path || 'asset/drive_disc/Unknown.webp'}" class="char-pool-avatar" style="height: 62px; object-fit: contain; padding: 4px;" alt="${set.name}">
                <div class="char-pool-name text-xs" style="font-size: 0.6rem; padding: 0.1rem 0;">${set.name}</div>
            `;

            // Set Drag events
            setCard.addEventListener("dragstart", (e) => {
                e.dataTransfer.setData("application/disc-set-id", set.id);
                e.dataTransfer.effectAllowed = "copyMove";
            });

            // Set click equips to currently active disc editor if possible, or offers prompt
            setCard.addEventListener("click", () => {
                // Instantly equip this set to all slots or let them know they can drop it
                applyDriveSetToAllSlots(set.id);
            });

            setGridPool.appendChild(setCard);
        });
    }
}

// =====================================================================
// 4. SQUAD MANAGEMENT WORKFLOWS
// =====================================================================
function equipCharacterToFirstAvailable(charId) {
    const charData = DB.characters[charId];
    if (!charData) return;

    // See if already in squad
    const existsIndex = squad.findIndex(s => s && s.characterId === charId);
    if (existsIndex !== -1) {
        // Swap active slot to it
        setActiveSlot(existsIndex);
        return;
    }

    // Find first empty
    let slotIndex = squad.findIndex(s => s === null);
    if (slotIndex === -1) {
        // Overwrite currently selected active builder slot
        slotIndex = activeSlotIndex;
    }

    // 优先使用当前 UID 导入的完整构筑；没有 UID 数据时才创建空白配置。
    const importedBuild = importedAccountBuilds.find(build => String(build.characterId) === String(charId));
    squad[slotIndex] = importedBuild ? JSON.parse(JSON.stringify(importedBuild)) : {
        characterId: charId,
        level: 60,
        cinema: 0,
        coreRank: 7,
        weaponId: getDefaultWeaponForCharacter(charData),
        weaponRefinement: 1,
        weaponPassiveActive: true,
        globalSubStats: {
            atk_pct: 0,
            crit_rate: 0,
            crit_dmg: 0,
            anomaly_prof: 0,
            pen_flat: 0,
            atk_flat: 0,
            hp_pct: 0,
            def_pct: 0,
            def_flat: 0,
            hp_flat: 0
        },
        driveDiscs: Array.from({ length: 6 }, (_, i) => ({
            setId: "",
            mainStat: getDefaultMainStat(i + 1),
            subStats: []
        }))
    };

    setActiveSlot(slotIndex);
}

function removeCharacterFromSquad(slotIndex) {
    squad[slotIndex] = null;
    
    // Choose another slot to make active if current got deleted
    if (activeSlotIndex === slotIndex) {
        const remaining = squad.findIndex(s => s !== null);
        activeSlotIndex = remaining !== -1 ? remaining : 0;
    }
    
    updateUI();
}

function setActiveSlot(slotIndex) {
    activeSlotIndex = slotIndex;
    
    // Auto-update weapon selectors to match character's W-Engine pool
    populateWeaponSelectForActive();
    
    updateUI();
}

function getDefaultWeaponForCharacter(charData) {
    if (charData && charData.id) {
        const charId = String(charData.id);
        if (charId.length >= 3) {
            const xx = charId.substring(charId.length - 3, charId.length - 1);
            const sId = "141" + xx;
            const aId = "131" + xx;
            if (DB.weapons[sId]) {
                return sId;
            } else if (DB.weapons[aId]) {
                return aId;
            }
        }
    }
    const specialty = charData ? charData.specialty : "";
    const matching = Object.values(DB.weapons).filter(w => w.specialty === specialty);
    if (matching.length > 0) {
        // Sort S > A > B rarity
        matching.sort((a, b) => b.rarity.localeCompare(a.rarity));
        return matching[0].id;
    }
    return "12001"; // Fallback to望
}

function getDefaultMainStat(slot) {
    if (slot === 1) return "生命值 (固定值)";
    if (slot === 2) return "攻击力 (固定值)";
    if (slot === 3) return "防御力 (固定值)";
    if (slot === 4) return "暴击率";
    if (slot === 5) return "属性伤害加成";
    if (slot === 6) return "攻击力百分比";
    return "";
}

function getElementEmoji(elem) {
    switch (elem) {
        case "火属性": return "🔥";
        case "冰属性": return "❄️";
        case "电属性": return "⚡";
        case "风属性": return "🌪️";
        case "物理": return "⚔️";
        case "以太": return "👾";
        default: return "✨";
    }
}

// =====================================================================
// 5. EVENT BINDINGS
// =====================================================================
function initEventBindings() {
    // Reset all buttons
    document.getElementById("btn-reset-all").addEventListener("click", () => {
        squad = [null, null, null];
        activeSlotIndex = 0;
        selectedCrisisBuffs.clear();
        stunnedState = false;
        const chkStun = document.getElementById("chk-stunned-state");
        if (chkStun) chkStun.checked = false;
        updateUI();
    });

    document.getElementById("btn-export-config").addEventListener("click", exportConfig);
    document.getElementById("btn-import-config").addEventListener("click", importConfig);

    // Roster Filters
    const elFilter = document.getElementById("filter-element");
    const specFilter = document.getElementById("filter-specialty");
    
    const applyFilters = () => {
        const el = elFilter.value;
        const spec = specFilter.value;
        
        const cards = document.querySelectorAll("#character-grid-pool .char-pool-card");
        cards.forEach(card => {
            const char = DB.characters[card.dataset.id];
            if (!char) return;
            
            const matchEl = !el || char.element === el;
            const matchSpec = !spec || char.specialty === spec;
            
            if (matchEl && matchSpec) {
                card.classList.remove("hidden");
            } else {
                card.classList.add("hidden");
            }
        });
    };
    
    elFilter.addEventListener("change", applyFilters);
    specFilter.addEventListener("change", applyFilters);

    // Active squad slots dropzones
    for (let i = 0; i < 3; i++) {
        const slotEl = document.getElementById(`squad-slot-${i}`);
        
        slotEl.addEventListener("dragover", (e) => {
            e.preventDefault();
            slotEl.classList.add("active-builder");
        });
        
        slotEl.addEventListener("dragleave", () => {
            slotEl.classList.remove("active-builder");
        });
        
        slotEl.addEventListener("drop", (e) => {
            e.preventDefault();
            slotEl.classList.remove("active-builder");
            const charId = e.dataTransfer.getData("text/plain");
            if (charId) {
                // Force equip to this specific slot
                const charData = DB.characters[charId];
                if (charData) {
                    const importedBuild = importedAccountBuilds.find(build => String(build.characterId) === String(charId));
                    squad[i] = importedBuild ? JSON.parse(JSON.stringify(importedBuild)) : {
                        characterId: charId,
                        level: 60,
                        cinema: 0,
                        coreRank: 7,
                        weaponId: getDefaultWeaponForCharacter(charData),
                        weaponRefinement: 1,
                        weaponPassiveActive: true,
                        driveDiscs: Array.from({ length: 6 }, (_, idx) => ({
                            setId: "",
                            mainStat: getDefaultMainStat(idx + 1),
                            subStats: [
                                { type: "none", rolls: 0 },
                                { type: "none", rolls: 0 },
                                { type: "none", rolls: 0 },
                                { type: "none", rolls: 0 }
                            ]
                        }))
                    };
                    setActiveSlot(i);
                }
            }
        });
        
        slotEl.addEventListener("click", () => {
            if (squad[i]) {
                setActiveSlot(i);
            }
        });
    }

    // Config Tab switches
    const tabButtons = document.querySelectorAll(".config-tabs .tab-btn");
    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tabButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            
            const tabId = btn.dataset.tab;
            document.querySelectorAll("#panel-gear-config .tab-content").forEach(tc => {
                tc.classList.add("hidden");
            });
            document.getElementById(tabId).classList.remove("hidden");
        });
    });

    // Tab A: Level, Cinema, Core Passive selects
    document.getElementById("select-char-cinema").addEventListener("change", (e) => {
        const activeChar = squad[activeSlotIndex];
        if (activeChar) {
            activeChar.cinema = parseInt(e.target.value);
            updateUI();
        }
    });
    
    document.getElementById("select-char-core").addEventListener("change", (e) => {
        const activeChar = squad[activeSlotIndex];
        if (activeChar) {
            activeChar.coreRank = parseInt(e.target.value);
            updateUI();
        }
    });

    // Tab B: Weapon Equips
    document.getElementById("select-equip-weapon").addEventListener("change", (e) => {
        const activeChar = squad[activeSlotIndex];
        if (activeChar) {
            activeChar.weaponId = e.target.value;
            updateUI();
            updateWeaponRosterActiveHighlights();
        }
    });

    document.getElementById("select-weapon-refinement").addEventListener("change", (e) => {
        const activeChar = squad[activeSlotIndex];
        if (activeChar) {
            activeChar.weaponRefinement = parseInt(e.target.value);
            updateUI();
        }
    });

    // Monster selector & stun checkbox
    document.getElementById("select-target-boss").addEventListener("change", (e) => {
        targetMonsterId = e.target.value;
        selectedCrisisBuffs.clear(); // Clear buffs of previous boss
        
        // Auto-fill stun base vulnerability
        const monster = DB.monsters[targetMonsterId];
        if (monster) {
            let stunBaseVal = 50;
            if (monster.name.includes("名可名")) {
                stunBaseVal = 25;
            } else if (monster.name.includes("冥宁芙")) {
                stunBaseVal = 100;
            } else if (monster.stun_extra_damage_taken_pct !== undefined) {
                stunBaseVal = monster.stun_extra_damage_taken_pct;
            }
            const stunBaseInput = document.getElementById("input-boss-stun-base");
            if (stunBaseInput) stunBaseInput.value = stunBaseVal;
        }
        
        updateUI();
    });

    const stunInput = document.getElementById("chk-stunned-state");
    if (stunInput) {
        stunInput.addEventListener("change", (e) => {
            stunnedState = e.target.checked;
            updateUI();
        });
    }

    // Stun base input listener
    const bossStunBaseInput = document.getElementById("input-boss-stun-base");
    if (bossStunBaseInput) {
        bossStunBaseInput.addEventListener("input", () => {
            updateUI();
        });
    }

    // Stage crisis buffs search input binding
    const searchCrisisBuffsInput = document.getElementById("input-search-crisis-buffs");
    if (searchCrisisBuffsInput) {
        searchCrisisBuffsInput.addEventListener("input", () => {
            const monster = DB.monsters[targetMonsterId];
            if (monster) {
                loadCrisisBuffsForMonster(monster.name);
            }
        });
    }

    // Monster Level Slider
    const bossLevelSlider = document.getElementById("input-target-level");
    const bossLevelLabel = document.getElementById("lbl-target-level");
    if (bossLevelSlider) {
        bossLevelSlider.addEventListener("input", (e) => {
            targetMonsterLevel = parseInt(e.target.value);
            if (targetMonsterLevel > 80) targetMonsterLevel = 80; // Strictly Cap at 80
            bossLevelLabel.textContent = `Lv.${targetMonsterLevel}`;
            updateUI();
        });
    }

    // Category Skill Nav buttons
    const catNavs = document.querySelectorAll("#skill-tabs-category .skill-tab-btn");
    catNavs.forEach(btn => {
        btn.addEventListener("click", () => {
            catNavs.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            activeSkillCategory = btn.dataset.cat;
            updateUI();
        });
    });

    // Skill level selector (lv12, lv14, lv16)
    document.getElementById("select-skill-level").addEventListener("change", (e) => {
        activeSkillLevel = e.target.value;
        updateUI();
    });
}

function populateWeaponSelectForActive() {
    const activeChar = squad[activeSlotIndex];
    const select = document.getElementById("select-equip-weapon");
    const gridPool = document.getElementById("weapon-grid-pool");
    if (!activeChar || !select || !gridPool) return;

    const charData = DB.characters[activeChar.characterId];
    if (!charData) return;

    // Filter W-Engines by character specialty
    const matchingWeapons = Object.values(DB.weapons).filter(w => w.specialty === charData.specialty);
    
    // Sort matching weapons S > A > B rarity
    matchingWeapons.sort((a, b) => b.rarity.localeCompare(a.rarity));

    // Populate dropdown
    select.innerHTML = "";
    matchingWeapons.forEach(w => {
        const opt = document.createElement("option");
        opt.value = w.id;
        opt.textContent = `[${w.rarity}级] ${w.name}`;
        select.appendChild(opt);
    });
    select.value = activeChar.weaponId;

    // Populate horizontal W-Engine Roster with images
    gridPool.innerHTML = "";
    matchingWeapons.forEach(w => {
        const card = document.createElement("div");
        card.className = `char-pool-card rarity-${w.rarity === 'S' ? 'S' : 'A'}`;
        card.style.flex = "0 0 86px";
        card.style.height = "86px";
        card.draggable = true;
        card.dataset.weaponId = w.id;
        
        card.innerHTML = `
            <img src="${w.icon_path || 'asset/weapon/Unknown.webp'}" class="char-pool-avatar" style="height: 62px; object-fit: contain; padding: 4px;" alt="${w.name}">
            <div class="char-pool-name text-xs" style="font-size: 0.6rem; padding: 0.1rem 0;">${w.name}</div>
        `;

        // Drag weapon W-Engine Card
        card.addEventListener("dragstart", (e) => {
            e.dataTransfer.setData("application/weapon-id", w.id);
            e.dataTransfer.effectAllowed = "copyMove";
        });

        // Click equips directly
        card.addEventListener("click", () => {
            activeChar.weaponId = w.id;
            select.value = w.id;
            updateUI();
            updateWeaponRosterActiveHighlights();
        });

        gridPool.appendChild(card);
    });

    // Make weapon card a drop zone
    const displayCard = document.getElementById("weapon-display-card");
    if (displayCard) {
        displayCard.addEventListener("dragover", (e) => e.preventDefault());
        displayCard.addEventListener("drop", (e) => {
            e.preventDefault();
            const draggedId = e.dataTransfer.getData("application/weapon-id");
            if (draggedId && DB.weapons[draggedId]) {
                activeChar.weaponId = draggedId;
                select.value = draggedId;
                updateUI();
                updateWeaponRosterActiveHighlights();
            }
        });
    }

    updateWeaponRosterActiveHighlights();
}

function updateWeaponRosterActiveHighlights() {
    const activeChar = squad[activeSlotIndex];
    if (!activeChar) return;
    
    document.querySelectorAll("#weapon-grid-pool .char-pool-card").forEach(card => {
        if (card.dataset.weaponId === activeChar.weaponId) {
            card.style.borderColor = "var(--clr-cyan)";
            card.style.boxShadow = "0 0 10px rgba(6, 182, 212, 0.4)";
        } else {
            card.style.borderColor = "";
            card.style.boxShadow = "";
        }
    });
}

function applyDriveSetToAllSlots(setId) {
    const activeChar = squad[activeSlotIndex];
    if (!activeChar) return;

    // Equip to all empty slots, or ask if they want to overwrite
    // For convenience: click fills all Slots (1-6) with this drive disc set!
    activeChar.driveDiscs.forEach(disc => {
        disc.setId = setId;
    });
    updateUI();
}

// =====================================================================
// 6. DYNAMIC UI RENDERER
// =====================================================================
function updateUI() {
    const activeChar = squad[activeSlotIndex];
    const headerHud = document.getElementById("app-header-hud");
    
    // Update squad counts in Header HUD
    const activeCount = squad.filter(s => s !== null).length;
    document.getElementById("hud-squad-count").textContent = `${activeCount} / 3`;
    
    const activeCharNameSpan = document.getElementById("hud-active-active-char") || document.getElementById("hud-active-char");
    if (activeChar) {
        const cData = DB.characters[activeChar.characterId];
        activeCharNameSpan.textContent = cData ? cData.name : "未选定";
        activeCharNameSpan.style.color = "var(--clr-cyan)";
    } else {
        activeCharNameSpan.textContent = "未配置";
        activeCharNameSpan.style.color = "";
    }

    // Render active squad slots cards
    squad.forEach((member, i) => {
        const slotEl = document.getElementById(`squad-slot-${i}`);
        if (!slotEl) return;
        
        slotEl.innerHTML = "";
        slotEl.classList.remove("active-builder", "empty");
        
        if (activeSlotIndex === i && member) {
            slotEl.classList.add("active-builder");
        }

        if (member) {
            const charData = DB.characters[member.characterId];
            slotEl.innerHTML = `
                <div class="slot-equipped-card">
                    <img src="${charData.icon_path || 'asset/character/Unknown.webp'}" class="slot-equipped-avatar" alt="${charData.name}">
                    <div class="slot-equipped-info">
                        <span class="slot-equipped-name">${charData.name}</span>
                        <span class="slot-equipped-sub">影画 ${member.cinema} / 核心 ${member.coreRank}</span>
                    </div>
                    <div class="slot-delete-btn" onclick="event.stopPropagation(); removeCharacterFromSquad(${i})">×</div>
                </div>
            `;
        } else {
            slotEl.classList.add("empty");
            slotEl.innerHTML = `
                <div class="slot-inner">
                    <div class="plus-icon">+</div>
                    <span class="slot-text">队员 ${i+1} (未配置)</span>
                </div>
            `;
        }
    });

    const gearPanel = document.getElementById("panel-gear-config");
    if (!activeChar) {
        gearPanel.classList.add("hidden");
        // Clear bottom settlement display
        document.getElementById("settlement-dashboard").innerHTML = `<div class="text-slate-400 text-center py-6">请先在上方配置小队并选择当前主控角色。</div>`;
        return;
    }

    // Show config details
    gearPanel.classList.remove("hidden");
    const activeCharData = DB.characters[activeChar.characterId];
    document.getElementById("active-char-config-title").textContent = `正在配置：${activeCharData.name} (${activeCharData.code_name})`;

    // Sync input selectors in Tab A
    document.getElementById("select-char-cinema").value = activeChar.cinema;
    document.getElementById("select-char-core").value = activeChar.coreRank;
    
    // Sync weapon refinement in Tab B
    const refineSelect = document.getElementById("select-weapon-refinement");
    if (refineSelect) refineSelect.value = activeChar.weaponRefinement;

    // Render active core passive ability information card in Tab A
    const rankInfo = activeCharData.passive ? activeCharData.passive[`level_${activeChar.coreRank}`] : null;
    const coreNameLabel = document.getElementById("info-core-name");
    const coreDescLabel = document.getElementById("info-core-desc");
    
    if (rankInfo) {
        coreNameLabel.innerHTML = `核心被动：${rankInfo.core_passive.name.replace("核心被动：", "")} <span class="badge badge-rarity">阶级 ${activeChar.coreRank}</span>`;
        
        let extraText = "";
        if (rankInfo.extra_ability) {
            extraText = `<br><br><strong class="highlight-text">【额外能力：${rankInfo.extra_ability.name.replace("额外能力：", "")}】</strong><br>${formatHtmlColors(rankInfo.extra_ability.desc)}`;
        }
        coreDescLabel.innerHTML = `${formatHtmlColors(rankInfo.core_passive.desc)}${extraText}`;
    } else {
        coreNameLabel.textContent = "核心被动说明";
        coreDescLabel.textContent = "暂无此等级的被动描述。";
    }

    // Render active shadow cinema description card in Tab A
    const cinemaCard = document.getElementById("info-cinema-card");
    const cinemaNameLabel = document.getElementById("info-cinema-name");
    const cinemaDescLabel = document.getElementById("info-cinema-desc");
    
    if (cinemaCard && cinemaNameLabel && cinemaDescLabel) {
        if (activeChar.cinema > 0 && activeCharData.mindscapes) {
            const cinemaKey = `cinema_${activeChar.cinema}`;
            const cinemaInfo = activeCharData.mindscapes[cinemaKey];
            if (cinemaInfo && cinemaInfo.name) {
                cinemaNameLabel.innerHTML = `影画 ${activeChar.cinema}：${cinemaInfo.name} <span class="badge" style="background-color: var(--clr-cyan); padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.75rem; color: #fff;">已激活</span>`;
                cinemaDescLabel.innerHTML = formatHtmlColors(cinemaInfo.desc);
                cinemaCard.style.display = "flex";
            } else {
                cinemaCard.style.display = "none";
            }
        } else {
            cinemaCard.style.display = "none";
        }
    }

    // Sync weapon configs in Tab B
    const weapData = DB.weapons[activeChar.weaponId];
    if (weapData) {
        document.getElementById("lbl-equipped-weapon-name").textContent = weapData.name;
        document.getElementById("badge-weapon-rarity").textContent = `${weapData.rarity}级音擎`;
        document.getElementById("img-equipped-weapon").src = weapData.icon_path || "asset/weapon/Unknown.webp";
        document.getElementById("val-weapon-base-atk").textContent = Math.floor(weapData.stats_lv60_star5.base_atk);
        
        const sec = weapData.stats_lv60_star5.secondary_stat;
        if (sec) {
            document.getElementById("lbl-weapon-sec-name").textContent = sec.name2;
            document.getElementById("val-weapon-sec-val").textContent = sec.format === "{0:0.#%}" ? `${sec.value}%` : sec.value;
        } else {
            document.getElementById("lbl-weapon-sec-name").textContent = "无";
            document.getElementById("val-weapon-sec-val").textContent = "—";
        }

        // Refinement passive info text
        const refinementText = weapData.refinements ? weapData.refinements[`refinement_${activeChar.weaponRefinement}`] : null;
        const effectName = document.getElementById("info-weapon-effect-name");
        const effectDesc = document.getElementById("info-weapon-effect-desc");
        
        if (refinementText) {
            effectName.innerHTML = `音擎效果：${refinementText.name} <span class="badge badge-rarity">精炼 ${activeChar.weaponRefinement}阶</span>`;
            effectDesc.innerHTML = formatHtmlColors(refinementText.desc);
        } else {
            effectName.textContent = "音擎被动效果";
            effectDesc.textContent = "无增益描述。";
        }
    }

    // Populate dynamic Drive Disc slots in Tab C
    renderDriveSlotsEditorList(activeChar);

    // Calculate final battle stats (Two-Pass squad pipeline)
    const { pass1Stats, pass2Stats } = calculateSquadCombatStats();
    const finalStats = pass2Stats[activeSlotIndex] || {
        hp: 0, atk: 0, def: 0, impact: 0, crit_rate: 5, crit_dmg: 50, pen_rate: 0, pen_flat: 0, anomaly_proficiency: 0, anomaly_mastery: 0, sp_recovery: 1.2, energy_regen: 100, attribute_dmg: 0, element: "物理", camp: "无"
    };
    const outStats = pass1Stats[activeSlotIndex] || {
        hp: 0, atk: 0, def: 0, impact: 0, crit_rate: 5, crit_dmg: 50, pen_rate: 0, pen_flat: 0, anomaly_proficiency: 0, anomaly_mastery: 0, sp_recovery: 1.2, energy_regen: 100, attribute_dmg: 0, element: "物理", camp: "无"
    };
    const webTeamState = buildWebTeamState(pass1Stats, activeChar);
    const displayFinalStats = webTeamState
        ? mergeWebPanelIntoLegacyStats(finalStats, webTeamState.activePanel)
        : finalStats;
    const displayPass2Stats = pass2Stats.map((stats, index) =>
        index === activeSlotIndex && webTeamState
            ? mergeWebPanelIntoLegacyStats(stats, webTeamState.activePanel)
            : stats,
    );
    renderLivePanelStats(outStats, displayFinalStats, webTeamState);

    // Update Stage Simulator UI (Boss details, resists, def)
    updateMonsterSimulator(displayFinalStats, webTeamState);

    // Render squad buffs selection panel
    renderSquadBuffsPanel(activeChar, displayPass2Stats);

    // Render expected damage and daze calculations table
    renderCombatSettlementEngine(activeChar, displayFinalStats, webTeamState);
}

function formatHtmlColors(str) {
    if (!str) return "";
    // Replaces ZZZ standard text coloring flags <color=#XXXXXX>text</color> with html span tags
    return str.replace(/<color=([^>]+)>/g, '<span style="color: $1; font-weight: 600;">').replace(/<\/color>/g, '</span>');
}

// =====================================================================
// 7. DRIVE DISC DYNAMIC PARTITIONS EDITOR
// =====================================================================
function renderDriveSlotsEditorList(activeChar) {
    const listContainer = document.getElementById("partitions-editor-list");
    if (!listContainer) return;

    // Save scroll position
    const scrollPos = listContainer.scrollTop;

    listContainer.innerHTML = "";
    
    // Drive set options
    let setOptionsHtml = `<option value="">-- 无套装 (None) --</option>`;
    if (DB.driveDiscs.sets) {
        Object.values(DB.driveDiscs.sets).forEach(s => {
            setOptionsHtml += `<option value="${s.id}">${s.name}</option>`;
        });
    }

    for (let slot = 1; slot <= 6; slot++) {
        // UID 数据可能明确返回 0/6 个驱动盘。编辑器仍需保留六个空槽位，
        // 不能因为缺少某个数组项而中断后续面板与伤害结算。
        const disc = activeChar.driveDiscs[slot - 1] || {
            setId: "",
            mainStat: "",
            subStats: [],
        };
        activeChar.driveDiscs[slot - 1] = disc;
        const row = document.createElement("div");
        row.className = "drive-slot-row";
        row.dataset.slotIndex = slot - 1;

        // Slot headers: disc set picker, main-stat picker
        let mainStatHtml = "";
        if (slot === 1) {
            mainStatHtml = `<span class="text-sm text-slate-300">生命值 (固定值: +2200)</span>`;
        } else if (slot === 2) {
            mainStatHtml = `<span class="text-sm text-slate-300">攻击力 (固定值: +316)</span>`;
        } else if (slot === 3) {
            mainStatHtml = `<span class="text-sm text-slate-300">防御力 (固定值: +184)</span>`;
        } else {
            // Selectable dropdown for Slots 4-6
            let optList = DB.driveDiscs.max_level_main_stats[`partition_${slot}`].options;
            let dropdown = `<select class="form-select slot-main-picker" data-slot="${slot}" style="padding: 0.15rem 0.5rem; font-size: 0.75rem;">`;
            Object.keys(optList).forEach(statName => {
                const selected = disc.mainStat === statName ? "selected" : "";
                dropdown += `<option value="${statName}" ${selected}>${statName} (+${optList[statName]})</option>`;
            });
            dropdown += `</select>`;
            mainStatHtml = dropdown;
        }

        let selectSetDropdown = `<select class="form-select slot-set-picker" data-slot="${slot}" style="padding: 0.15rem 0.5rem; font-size: 0.75rem; width: 130px;">` + setOptionsHtml + `</select>`;

        row.innerHTML = `
            <div class="slot-row-header" style="margin-bottom: 0;">
                <span class="slot-badge-circle">${slot}</span>
                ${selectSetDropdown}
                <div class="flex items-center gap-1">${mainStatHtml}</div>
            </div>
        `;

        // Make disc slot row a dropzone for Set Pool drags
        row.addEventListener("dragover", (e) => {
            e.preventDefault();
            row.style.background = "rgba(6, 182, 212, 0.1)";
            row.style.borderColor = "var(--clr-cyan)";
        });

        row.addEventListener("dragleave", () => {
            row.style.background = "";
            row.style.borderColor = "";
        });

        row.addEventListener("drop", (e) => {
            e.preventDefault();
            row.style.background = "";
            row.style.borderColor = "";
            const setId = e.dataTransfer.getData("application/disc-set-id");
            if (setId && DB.driveDiscs.sets[setId]) {
                disc.setId = setId;
                updateUI();
            }
        });

        // Set sets dropdown selections
        const setSelect = row.querySelector(".slot-set-picker");
        setSelect.value = disc.setId;
        setSelect.addEventListener("change", (e) => {
            disc.setId = e.target.value;
            updateUI();
        });

        // Set Slot 4-6 main stat dropdowns selections
        if (slot >= 4) {
            const mainSelect = row.querySelector(".slot-main-picker");
            mainSelect.addEventListener("change", (e) => {
                disc.mainStat = e.target.value;
                updateUI();
            });
        }

        listContainer.appendChild(row);
    }

    // Set scroll position back
    listContainer.scrollTop = scrollPos;

    // Call global sub-stats allocator renderer
    renderGlobalSubstatsAllocator(activeChar);
}

// =====================================================================
// 8. COMBAT STATISTICS CALCULATION ENGINE
// =====================================================================
function calculateFinalStatsPass1(member) {
    const charData = DB.characters[member.characterId];
    const weaponData = DB.weapons[member.weaponId];

    if (!charData) {
        return {
            hp: 0, atk: 0, def: 0, impact: 0, crit_rate: 5, crit_dmg: 50, pen_rate: 0, pen_flat: 0, anomaly_proficiency: 0, anomaly_mastery: 0, energy_regen: 100, attribute_dmg: 0, element: "物理", camp: "无"
        };
    }

    // 1. Initialize Base stats
    const stats = {
        hp: charData.stats.hp,
        atk: charData.stats.atk,
        def: charData.stats.def,
        impact: charData.stats.impact,
        crit_rate: charData.stats.crit_rate,
        crit_dmg: charData.stats.crit_dmg,
        pen_rate: charData.stats.pen_rate,
        pen_flat: 0,
        pen_dmg_bonus: 0,
        anomaly_proficiency: charData.stats.anomaly_proficiency,
        anomaly_mastery: charData.stats.anomaly_mastery,
        sp_recovery: charData.stats.sp_recovery || 1.2,
        energy_regen: 100, // base 100%
        attribute_dmg: 0   // base 0%
    };

    // Keep base references
    const baseAtk = stats.atk + (weaponData ? Math.floor(weaponData.stats_lv60_star5.base_atk) : 0);
    const baseHp = stats.hp;
    const baseDef = stats.def;
    const baseImpact = stats.impact;

    let atkPct = 0;
    let hpPct = 0;
    let defPct = 0;
    let impactPct = 0;
    let anomaly_mastery_pct = 0;
    let anomaly_mastery_flat = 0;

    // 2. Add weapon secondary stat if matching
    if (weaponData && weaponData.stats_lv60_star5.secondary_stat) {
        const sec = weaponData.stats_lv60_star5.secondary_stat;
        const name = sec.name2;
        const val = sec.value;

        switch (name) {
            case "攻击力百分比": atkPct += val; break;
            case "生命值百分比": hpPct += val; break;
            case "防御力百分比": defPct += val; break;
            case "暴击率": stats.crit_rate += val; break;
            case "暴击伤害": stats.crit_dmg += val; break;
            case "穿透率": stats.pen_rate += val; break;
            case "异常精通": stats.anomaly_proficiency += val; break;
            case "冲击力": impactPct += val; break;
            case "能量自动回复": stats.energy_regen += val; break;
            case "异常掌控": anomaly_mastery_pct += val; break;
        }
    }

    // 4. Set bonuses detector
    const setCounts = {};
    member.driveDiscs.forEach(disc => {
        if (disc.setId) {
            setCounts[disc.setId] = (setCounts[disc.setId] || 0) + 1;
        }
    });

    const activeSetDescriptions = [];
    Object.keys(setCounts).forEach(setId => {
        const count = setCounts[setId];
        const setMeta = DB.driveDiscs.sets[setId];
        if (!setMeta) return;

        if (count >= 2) {
            const bonus = getSet2PcBonus(setId, charData.element);
            if (bonus.atk_pct) atkPct += bonus.atk_pct;
            if (bonus.hp_pct) hpPct += bonus.hp_pct;
            if (bonus.def_pct) defPct += bonus.def_pct;
            if (bonus.crit_rate) stats.crit_rate += bonus.crit_rate;
            if (bonus.crit_dmg) stats.crit_dmg += bonus.crit_dmg;
            if (bonus.pen_rate) stats.pen_rate += bonus.pen_rate;
            if (bonus.anomaly_proficiency) stats.anomaly_proficiency += bonus.anomaly_proficiency;
            if (bonus.energy_regen) stats.energy_regen += bonus.energy_regen;
            if (bonus.impact) impactPct += bonus.impact;
            if (bonus.anomaly_mastery) anomaly_mastery_pct += bonus.anomaly_mastery;
            if (bonus.attribute_dmg) stats.attribute_dmg += bonus.attribute_dmg;

            if (member === squad[activeSlotIndex]) {
                activeSetDescriptions.push({
                    name: setMeta.name,
                    type: "2件套",
                    desc: setMeta.desc2
                });
            }
        }

        if (count >= 4) {
            if (member === squad[activeSlotIndex]) {
                activeSetDescriptions.push({
                    name: setMeta.name,
                    type: "4件套",
                    desc: setMeta.desc4
                });
            }
        }
    });

    if (member === squad[activeSlotIndex]) {
        renderActiveSetsStatus(activeSetDescriptions);
    }

    // 5. Drive Disc Main stats
    member.driveDiscs.forEach((disc, slotIdx) => {
        const slot = slotIdx + 1;
        if (slot === 1) stats.hp += 2200;
        else if (slot === 2) stats.atk += 316;
        else if (slot === 3) stats.def += 184;
        else if (disc.mainStat) {
            const optList = DB.driveDiscs.max_level_main_stats[`partition_${slot}`].options;
            const mainValStr = optList[disc.mainStat];
            const mainVal = parseFloat(mainValStr);
            
            switch (disc.mainStat) {
                case "攻击力百分比": atkPct += mainVal; break;
                case "生命值百分比": hpPct += mainVal; break;
                case "防御力百分比": defPct += mainVal; break;
                case "暴击率": stats.crit_rate += mainVal; break;
                case "暴击伤害": stats.crit_dmg += mainVal; break;
                case "异常精通": stats.anomaly_proficiency += mainVal; break;
                case "穿透率": stats.pen_rate += mainVal; break;
                case "属性伤害加成": stats.attribute_dmg += mainVal; break;
                case "冲击力": impactPct += mainVal; break;
                case "能量自动回复": stats.energy_regen += mainVal; break;
                case "异常掌控": anomaly_mastery_pct += mainVal; break;
            }
        }
    });

    // 6. Global Substats Allocator
    if (member.globalSubStats) {
        Object.keys(member.globalSubStats).forEach(key => {
            const rolls = member.globalSubStats[key] || 0;
            if (rolls <= 0) return;
            const val = S_SUBSTAT_VALUES[key] * rolls;
            switch (key) {
                case "atk_pct": atkPct += val; break;
                case "hp_pct": hpPct += val; break;
                case "def_pct": defPct += val; break;
                case "crit_rate": stats.crit_rate += val; break;
                case "crit_dmg": stats.crit_dmg += val; break;
                case "anomaly_prof": stats.anomaly_proficiency += val; break;
                case "pen_flat": stats.pen_flat += val; break;
                case "atk_flat": stats.atk += val; break;
                case "hp_flat": stats.hp += val; break;
                case "def_flat": stats.def += val; break;
            }
        });
    }

    // 6.5 Hidden Core Passive Increments Rule
    if (member.coreRank) {
        const coreLayers = Math.floor(member.coreRank / 2);
        if (coreLayers > 0) {
            if (member.characterId === "1491") { // 千夏
                atkPct += coreLayers * 7.0;
            } else if (member.characterId === "1341") { // 照
                hpPct += coreLayers * 6.0;
            } else if (member.characterId === "1441") { // 狛野真斗
                hpPct += coreLayers * 6.0;
            }
        }
    }

    // 7. Sum up final stats percentages
    stats.atk = baseAtk * (1 + atkPct / 100) + (stats.atk - charData.stats.atk);
    stats.hp = baseHp * (1 + hpPct / 100) + (stats.hp - charData.stats.hp);
    stats.def = baseDef * (1 + defPct / 100) + (stats.def - charData.stats.def);
    stats.impact = baseImpact * (1 + impactPct / 100);
    const baseAnomalyMastery = charData.stats.anomaly_mastery || 120;
    stats.anomaly_mastery = baseAnomalyMastery * (1 + anomaly_mastery_pct / 100) + anomaly_mastery_flat;

    // Save base references for Soukaku style (base character ATK + weapon base ATK)
    stats.baseAtk = baseAtk;
    stats.element = charData.element;
    stats.camp = charData.camp ? Object.values(charData.camp)[0] : "无";

    return stats;
}

function getSquadStunVulnerability() {
    let list = [];
    squad.forEach(member => {
        if (!member) return;
        const charId = member.characterId;
        const charData = DB.characters[charId];
        if (!charData) return;

        let val = 0;
        let note = "";

        if (charId === "1251") { // 青衣
            if (member.cinema >= 2) {
                val = 108;
                note = "影画 2 级增幅";
            } else {
                val = 80;
                note = "基础核心";
            }
        } else if (charId === "1491") { // 千夏
            val = 30;
        } else if (charId === "1511") { // 南宫羽
            val = 30;
        } else if (charId === "1481") { // 琉音
            val = 30;
        } else if (charId === "1141") { // 莱卡恩
            val = 35;
        } else if (charId === "1101") { // 珂蕾妲
            val = 35;
        } else if (charId === "1161") { // 莱特
            val = 30;
        } else if (charId === "1361") { // 扳机
            if (member.cinema >= 1) {
                val = 55;
                note = "影画1 常态全覆盖";
            } else {
                val = 35;
                note = "核心常态全覆盖";
            }
        }

        if (val > 0) {
            list.push({
                charId: charId,
                name: charData.name,
                value: val,
                note: note
            });
        }
    });
    return list;
}

function applyImportedReportedPanel(stats, member) {
    if (!stats || !member || !Array.isArray(member.reportedPanel)) return stats;

    const panelById = new Map(
        member.reportedPanel.map(property => [Number(property.propertyId), Number(property.final)])
    );
    const assign = (propertyId, key) => {
        const value = panelById.get(propertyId);
        if (Number.isFinite(value)) stats[key] = value;
    };

    // 米游社返回的是局外最终面板；局内 Buff 仍在 pass2 / 新版队伍桥接中叠加。
    assign(1, "hp");
    assign(2, "atk");
    assign(3, "def");
    assign(4, "impact");
    assign(5, "crit_rate");
    assign(6, "crit_dmg");
    assign(7, "anomaly_mastery");
    assign(8, "anomaly_proficiency");
    assign(9, "pen_rate");
    // 米游社 property 11 是最终每秒回复值（例如 1.20），不是旧页面内部
    // 使用的 100% 能量回复倍率。
    assign(11, "sp_recovery");
    assign(232, "pen_flat");

    const elementDamagePropertyIds = {
        "物理": 315,
        "火属性": 316,
        "冰属性": 317,
        "电属性": 318,
        "以太": 319,
        "风属性": 320
    };
    const elementDamagePropertyId = elementDamagePropertyIds[stats.element];
    if (elementDamagePropertyId !== undefined) {
        assign(elementDamagePropertyId, "attribute_dmg");
    }
    return stats;
}

function getSet4PcBuffs(setId, specialty, providerPass1 = null) {
    const buffs = {
        self: {},
        team: {}
    };
    if (!setId) return buffs;

    switch (setId) {
        case "31000": // 啄木鸟电音
            buffs.self.atk_pct = 27.0; // 叠满3层，每层9% => 27%
            break;
        case "31100": // 河豚电音
            buffs.self.atk_pct = 15.0; // 终结技施放后攻击力+15%
            buffs.self.dmg_bonus = 20.0; // 终结技伤害提升20%
            buffs.self.tags = ["chain"];
            break;
        case "31200": // 震星迪斯科
            buffs.self.daze_bonus = 20.0; // 普攻/冲刺/闪避反击主要目标失衡值+20%
            buffs.self.tags = ["basic", "dodge"];
            break;
        case "31300": // 自由蓝调
            // 降低属性异常积蓄抗性，对战斗面板无直接静态属性加成
            break;
        case "31400": // 激素朋克
            buffs.self.atk_pct = 25.0; // 接战时攻击力+25%
            break;
        case "31500": // 灵魂摇滚
            // 损失生命时伤害降低40% (防御机制)
            break;
        case "31600": // 摇摆爵士
            buffs.team.dmg_bonus = 15.0; // 连携或终结技时全队增伤15%
            break;
        case "31800": // 混沌爵士
            buffs.self.dmg_bonus = 15.0; // 火和电属性伤害+15%
            buffs.self.tags = ["fire", "electric", "special", "assist"]; // 后场强化特殊技/支援攻击额外加成
            break;
        case "31900": // 原始朋克
            buffs.team.dmg_bonus = 15.0; // 招架或回避支援时全队增伤15%
            break;
        case "32200": // 炎狱重金属
            buffs.self.crit_rate = 28.0; // 灼烧状态下暴击率+28%
            break;
        case "32300": // 混沌重金属
            buffs.self.crit_dmg = 53.0; // 暴伤+20%，触发侵蚀时额外最多叠满6层共+33%，共+53%
            break;
        case "32400": // 雷暴重金属
            buffs.self.atk_pct = 28.0; // 目标感电时攻击力+28%
            break;
        case "32500": // 极地重金属
            buffs.self.dmg_bonus = 40.0; // 普攻/冲刺攻击+20%，施加冻结/碎冰额外+20%，共+40%
            buffs.self.tags = ["basic"];
            break;
        case "32600": // 獠牙重金属
            buffs.self.dmg_bonus = 35.0; // 施加强击后，对目标伤害提升35%
            break;
        case "32700": // 折枝剑歌
            buffs.self.crit_dmg = 30.0; // 异常掌控>=115时暴伤+30%
            buffs.self.crit_rate = 12.0; // 冻结/碎冰时暴击率+12%
            break;
        case "32800": // 静听嘉音
            buffs.team.dmg_bonus = 24.0; // 快速支援全队伤害+24% (叠满3层)
            break;
        case "32900": // 如影相随
            buffs.self.atk_pct = 12.0; // 叠满3层攻击力+12%
            buffs.self.crit_rate = 12.0; // 叠满3层暴击率+12%
            break;
        case "33000": // 法厄同之歌
            buffs.self.anomaly_proficiency = 45.0; // 异常精通+45
            buffs.self.dmg_bonus = 25.0; // 造成的以太伤害提升25%
            buffs.self.tags = ["ether"];
            break;
        case "33100": // 云岿如我
            buffs.self.crit_rate = 12.0; // 强化特殊技/连携/终结技时暴击率+12%
            buffs.self.pen_dmg_bonus = 10.0; // 贯穿伤害提升10% (叠满3层)
            break;
        case "33200": // 山大王
            if (specialty === "击破") {
                const critRate = (providerPass1 && providerPass1.crit_rate) || 0;
                buffs.team.crit_dmg = critRate >= 50.0 ? 30.0 : 15.0;
            }
            break;
        case "33300": // 拂晓生花
            buffs.self.dmg_bonus = 40.0; // 普攻伤害提升20%，如果是强攻角色开启强化特殊/终结技额外+20%，共+40%普攻伤害
            buffs.self.tags = ["basic"];
            break;
        case "33400": // 月光骑士颂
            if (specialty === "支援") {
                buffs.team.dmg_bonus = 18.0; // 支援角色发动强化特殊/终结技时全队增伤18%
            }
            break;
        case "33500": // 沧浪行歌
            buffs.self.crit_rate = 20.0; // 处于以太帷幕时暴击率+10%，强攻开启/延长帷幕额外+10%，共+20%
            buffs.self.atk_pct = 10.0; // 强攻开启/延长帷幕攻击力+10%
            break;
        case "33600": // 流光咏叹
            buffs.self.anomaly_proficiency = 36.0; // 普攻命中异常精通+36
            buffs.self.dmg_bonus = 25.0; // 敌人进入失衡状态时伤害提升25%
            break;
        case "33700": // 雪兔梦游仙境
            if (specialty === "防护") {
                buffs.team.dmg_bonus = 18.0; // 防护角色发动强化特殊或招架/回避支援，全队增伤18%
            }
            break;
        case "33800": // 囚徒手记
            buffs.self.anomaly_proficiency = 48.0; // 异常精通+48
            buffs.self.dmg_bonus = 16.0; // 触发冻结时异常和紊乱伤害提升16%
            buffs.self.tags = ["anomaly"];
            break;
        case "33900": // 呼啸沙龙
            buffs.self.anomaly_proficiency = 50.0; // 异常精通提升50点
            buffs.self.dmg_bonus = 18.0; // 触发风化后造成的伤害提升18%
            break;
        case "34000": // 拂晓行纪
            buffs.self.crit_dmg = 30.0; // 以太伤害暴击伤害提升30%
            buffs.self.tags = ["ether"];
            buffs.self.atk_pct = 10.0; // 释放强化特殊/终结技时攻击力提升10%
            break;
    }
    return buffs;
}

function applySet4PcStat(stats, statKey, val, tags = null) {
    if (statKey === "crit_rate") stats.crit_rate += val;
    else if (statKey === "crit_dmg") stats.crit_dmg += val;
    else if (statKey === "dmg_bonus") {
        if (tags && tags.length > 0) {
            // 兼容旧的 anomaly 标签：同时给两个轨道加数值
            if (tags.includes("anomaly")) {
                stats.pure_anomaly_dmg_bonus = (stats.pure_anomaly_dmg_bonus || 0) + val;
                stats.disorder_dmg_bonus = (stats.disorder_dmg_bonus || 0) + val;
            }
            // 新增的独立标签
            if (tags.includes("pure_anomaly")) {
                stats.pure_anomaly_dmg_bonus = (stats.pure_anomaly_dmg_bonus || 0) + val;
            }
            if (tags.includes("disorder")) {
                stats.disorder_dmg_bonus = (stats.disorder_dmg_bonus || 0) + val;
            }
            
            stats.tagged_dmg_bonuses.push({
                tags: tags,
                value: val
            });
        } else {
            stats.attribute_dmg += val;
        }
    }
    else if (statKey === "pen_dmg_bonus") stats.pen_dmg_bonus = (stats.pen_dmg_bonus || 0) + val;
    else if (statKey === "atk_pct") stats.combatAtkPctIn += val;
    else if (statKey === "atk_flat") stats.combatAtkFlatIn += val;
    else if (statKey === "def_pct") stats.combatDefPctIn += val;
    else if (statKey === "def_flat") stats.combatDefFlatIn += val;
    else if (statKey === "hp_pct") stats.combatHpPctIn += val;
    else if (statKey === "hp_flat") stats.combatHpFlatIn += val;
    else if (statKey === "pen_rate") stats.pen_rate += val;
    else if (statKey === "pen_flat") stats.pen_flat += val;
    else if (statKey === "anomaly_proficiency") stats.anomaly_proficiency += val;
    else if (statKey === "energy_regen") stats.energy_regen += val;
    else if (statKey === "impact") stats.combatImpactPctIn += val;
    else if (statKey === "daze_bonus") {
        if (tags && tags.length > 0) {
            stats.tagged_daze_bonuses.push({
                tags: tags,
                value: val
            });
        } else {
            stats.daze_bonus += val;
        }
    }
}

const CHARACTER_FACTIONS_MAP = {
    // 狡兔屋 (Cunning Hares)
    "1011": "狡兔屋", "1021": "狡兔屋", "1031": "狡兔屋", "1041": "狡兔屋",
    // 白祇重工 (Belobog)
    "1101": "白祇重工", "1111": "白祇重工", "1121": "白祇重工", "1131": "白祇重工",
    // 维多利亚家政 (Victoria)
    "1141": "维多利亚家政", "1151": "维多利亚家政", "1181": "维多利亚家政", "1191": "维多利亚家政",
    // 卡吕冬之子 (Sons of Calydon)
    "1071": "卡吕冬之子", "1171": "卡吕冬之子", "1061": "卡吕冬之子", "1161": "卡吕冬之子",
    // 对空六课 (Section 6)
    "1201": "对空六课", "1211": "对空六课", "1221": "对空六课", "1231": "对空六课",
    // 治安局 (NEPS)
    "1241": "治安局", "1251": "治安局", "1261": "治安局", "1271": "治安局",
    // 新艾利都 (New Eridu)
    "1341": "新艾利都", "1411": "新艾利都", "1451": "新艾利都", "1521": "新艾利都", "1541": "新艾利都",
    // 妄想天使 (Delusional Angels)
    "1491": "妄想天使", "1501": "妄想天使", "1511": "妄想天使"
};

function isSquadActiveExtraAbility(member, squad) {
    if (!member) return false;
    const charId = member.characterId;
    const charData = DB.characters[charId];
    if (!charData) return false;

    // Find other members in the squad
    const otherMembers = squad.filter(m => m && m.characterId !== charId);
    if (otherMembers.length === 0) return false;

    const myElement = charData.stats.element || charData.element || ""; 
    const mySpecialty = charData.specialty || "";
    const myCamp = CHARACTER_FACTIONS_MAP[charId] || "无";

    for (const other of otherMembers) {
        const otherData = DB.characters[other.characterId];
        if (!otherData) continue;

        const otherElement = otherData.stats.element || otherData.element || "";
        const otherSpecialty = otherData.specialty || "";
        const otherCamp = CHARACTER_FACTIONS_MAP[other.characterId] || "无";

        // Same element
        if (myElement && otherElement && myElement === otherElement) return true;

        // Same specialty
        if (mySpecialty && otherSpecialty && mySpecialty === otherSpecialty) return true;

        // Same faction
        if (myCamp && otherCamp && myCamp !== "无" && myCamp === otherCamp) return true;

        // Alice Special Case: Anomaly + Support or Anomaly
        if (charId === "1401" && (otherSpecialty === "异常" || otherSpecialty === "支援")) {
            return true;
        }
        // Caesar Special Case: Defense + Faction or Defense
        if (charId === "1071" && (otherSpecialty === "防护" || otherSpecialty === "defense")) {
            return true;
        }
    }

    return false;
}

function checkAndForceSquadExtraAbilities() {
    squad.forEach(member => {
        if (!member) return;
        const charId = member.characterId;
        const config = CHAR_BUFFS_CONFIG[charId];
        if (!config) return;

        const extraActive = isSquadActiveExtraAbility(member, squad);

        if (config.self_buffs) {
            config.self_buffs.forEach(buff => {
                if (buff.name.includes("额外能力") || buff.id.includes("extra")) {
                    activeBuffsState[buff.id] = extraActive;
                }
            });
        }
        if (config.team_buffs) {
            config.team_buffs.forEach(buff => {
                if (buff.name.includes("额外能力") || buff.id.includes("extra")) {
                    activeBuffsState[buff.id] = extraActive;
                }
            });
        }
    });
}

function calculateSquadCombatStats() {
    const activeChar = squad[activeSlotIndex];
    // Force recalculate and enforce active states of Extra Abilities based on current squad
    checkAndForceSquadExtraAbilities();

    // Pass 1: Independent Standalone calculations for each slot (representing city/out-of-combat stats)
    const pass1Stats = squad.map(member => {
        if (!member) return null;
        return applyImportedReportedPanel(calculateFinalStatsPass1(member), member);
    });

    // Pass 2: Apply accumulated static and provider-linked dynamic buffs to each active character
    const pass2Stats = squad.map((member, idx) => {
        if (!member) return null;

        // Start with Pass 1 copy
        const stats = JSON.parse(JSON.stringify(pass1Stats[idx]));

        // Initialize in-combat variables for tracking
        stats.combatAtkPctIn = 0;
        stats.combatAtkFlatIn = 0;
        stats.combatHpPctIn = 0;
        stats.combatHpFlatIn = 0;
        stats.combatDefPctIn = 0;
        stats.combatDefFlatIn = 0;
        stats.combatImpactPctIn = 0;
        stats.combatImpactFlatIn = 0;

        stats.daze_bonus = 0;
        stats.tagged_dmg_bonuses = [];
        stats.tagged_daze_bonuses = [];
        stats.tagged_ignore_def_bonuses = [];
        stats.def_shred = 0;
        stats.ignore_def = 0;
        stats.stun_vuln = 0;
        stats.additional_multipliers = [];
        stats.multiplier_ratios = [];
        stats.shield_flat = 0;
        stats.pure_anomaly_dmg_bonus = 0; // 新增：只拐强击/感电/灼烧等
        stats.disorder_dmg_bonus = 0; // 新增：只拐紊乱
        stats.disorder_ratio_bonus = 0;
        stats.res_shred = 0;
        const charId = member.characterId;
        const charData = DB.characters[charId];
        const weaponData = DB.weapons[member.weaponId];
        if (!charData) return stats;

        stats.pen_dmg_bonus = stats.pen_dmg_bonus || 0;
        if (charData.specialty === "命破") {
            stats.breach_power = 0;
        }

        // A. Apply active character's 4pc self-buffs
        const setCounts = {};
        member.driveDiscs.forEach(disc => {
            if (disc.setId) {
                setCounts[disc.setId] = (setCounts[disc.setId] || 0) + 1;
            }
        });

        Object.keys(setCounts).forEach(setId => {
            const count = setCounts[setId];
            if (count >= 4) {
                const buffs = getSet4PcBuffs(setId, charData.specialty, pass1Stats[idx]);
                const buffId = `4pc-${charId}-${setId}`;
                if (activeBuffsState[buffId] === undefined) {
                    activeBuffsState[buffId] = true;
                }
                if (activeBuffsState[buffId]) {
                    if (buffs.self) {
                        const tags = buffs.self.tags || null;
                        Object.keys(buffs.self).forEach(statKey => {
                            if (statKey !== "tags") {
                                applySet4PcStat(stats, statKey, buffs.self[statKey], tags);
                            }
                        });
                    }
                    if (buffs.team) {
                        const tags = buffs.team.tags || null;
                        Object.keys(buffs.team).forEach(statKey => {
                            if (statKey !== "tags") {
                                applySet4PcStat(stats, statKey, buffs.team[statKey], tags);
                            }
                        });
                    }
                }
            }
        });

        // C. Apply self static & dynamic buffs configured in CHAR_BUFFS_CONFIG
        const config = CHAR_BUFFS_CONFIG[charId];
        if (config && config.self_buffs) {
            let selfStaticModifiers = {};
            config.self_buffs.forEach(buff => {
                if (buff.cinema_req && member.cinema < buff.cinema_req) return;
                if (activeBuffsState[buff.id] === undefined) {
                    activeBuffsState[buff.id] = buff.active !== false;
                }
                if (activeBuffsState[buff.id] && buff.dynamic_modifier) {
                    selfStaticModifiers[buff.dynamic_modifier.target_buff_id] = buff.dynamic_modifier;
                }
            });

            config.self_buffs.forEach(buff => {
                // Skip cinema-gated buffs if cinema level is insufficient
                if (buff.cinema_req && member.cinema < buff.cinema_req) return;
                if (activeBuffsState[buff.id]) {
                    const modifier = selfStaticModifiers[buff.id] || null;
                    applyBuffEffect(stats, buff, pass1Stats[idx], modifier);
                }
            });
        }

        // E. Apply teammate support buffs (including own team buffs)
        squad.forEach((teammate, tIdx) => {
            if (!teammate) return;

            const tCharId = teammate.characterId;
            const tCharData = DB.characters[tCharId];
            const teammateConfig = CHAR_BUFFS_CONFIG[tCharId];
            if (!tCharData) return;

            // E1. Configured teammate team buffs (including own team buffs!)
            if (teammateConfig && teammateConfig.team_buffs) {
                let teammateStaticModifiers = {};
                teammateConfig.team_buffs.forEach(buff => {
                    if (buff.cinema_req && teammate.cinema < buff.cinema_req) return;
                    if (activeBuffsState[buff.id] === undefined) {
                        activeBuffsState[buff.id] = buff.active !== false;
                    }
                    if (activeBuffsState[buff.id] && buff.dynamic_modifier) {
                        teammateStaticModifiers[buff.dynamic_modifier.target_buff_id] = buff.dynamic_modifier;
                    }
                });

                teammateConfig.team_buffs.forEach(buff => {
                    // Skip cinema-gated buffs if teammate cinema level is insufficient
                    if (buff.cinema_req && teammate.cinema < buff.cinema_req) return;
                    if (buff.id === "luxia_core_hp" && activeBuffsState["zhao_team_shield_atk"]) {
                        return;
                    }
                    if (activeBuffsState[buff.id]) {
                        const providerPass1 = pass1Stats[tIdx];
                        const modifier = teammateStaticModifiers[buff.id] || null;
                        applyBuffEffect(stats, buff, providerPass1, modifier);
                    }
                });
            }

            // E2. Teammate's 4pc set team buffs (SKIP for self as it is already applied in section A!)
            if (tIdx !== idx) {
                const tSetCounts = {};
                teammate.driveDiscs.forEach(disc => {
                    if (disc.setId) {
                        tSetCounts[disc.setId] = (tSetCounts[disc.setId] || 0) + 1;
                    }
                });

                Object.keys(tSetCounts).forEach(setId => {
                    const count = tSetCounts[setId];
                    if (count >= 4) {
                        const buffs = getSet4PcBuffs(setId, tCharData.specialty, pass1Stats[tIdx]);
                        const buffId = `4pc-${tCharId}-${setId}`;
                        if (activeBuffsState[buffId] === undefined) {
                            activeBuffsState[buffId] = true;
                        }
                        if (activeBuffsState[buffId]) {
                            if (buffs.team) {
                                const tags = buffs.team.tags || null;
                                Object.keys(buffs.team).forEach(statKey => {
                                    if (statKey !== "tags") {
                                        applySet4PcStat(stats, statKey, buffs.team[statKey], tags);
                                    }
                                });
                            }
                        }
                    }
                });
            }
        });

        // F. Apply W-Engine Signature Passives (归位！)
        const weaponConfig = WEAPON_BUFFS_CONFIG[member.weaponId];
        if (weaponConfig && weaponConfig.self_buffs) {
            weaponConfig.self_buffs.forEach(baseBuff => {
                const currentBuff = resolveWeaponBuff(baseBuff, member.weaponRefinement);
                if (activeBuffsState[currentBuff.id] === undefined) {
                    activeBuffsState[currentBuff.id] = currentBuff.active !== false;
                }
                if (activeBuffsState[currentBuff.id]) {
                    // 这里统一使用 pass1Stats
                    applyBuffEffect(stats, currentBuff, pass1Stats[idx]);
                }
            });
        }

        // G. Apply Boss Field Environment effects
        const monster = DB.monsters[targetMonsterId];
        if (monster) {
            Object.keys(BOSS_FIELD_BUFFS).forEach(key => {
                if (monster.name.includes(key)) {
                    const fieldBuff = BOSS_FIELD_BUFFS[key];
                    if (fieldBuff.has_crit_dmg_stacks) {
                        stats.crit_dmg += bossFieldCritDmgStacks * fieldBuff.crit_dmg_per_stack;
                    }
                }
            });
        }

        // Delusional Ensemble flat ATK addition:
        const isChinatsuActive = activeBuffsState["chinatsu_extra_vuln"] || false;
        const isAireiActive = activeBuffsState["airei_ether_veil"] || false;
        const isNangongyuActive = activeBuffsState["nangongyu_ether_veil"] || false;
        if (isChinatsuActive || isAireiActive || isNangongyuActive) {
            stats.combatAtkFlatIn += 50.0;
        }

        // Finalize In-Combat Stats
        stats.atk = stats.atk * (1 + stats.combatAtkPctIn / 100) + stats.combatAtkFlatIn;
        stats.hp = stats.hp * (1 + stats.combatHpPctIn / 100) + stats.combatHpFlatIn;
        stats.def = stats.def * (1 + stats.combatDefPctIn / 100) + stats.combatDefFlatIn;
        stats.impact = stats.impact * (1 + stats.combatImpactPctIn / 100) + stats.combatImpactFlatIn;

        if (charData.specialty === "命破") {
            stats.breach_power = 0.3 * stats.atk + 0.1 * stats.hp + stats.breach_power;
        }

        // H. Apply realtime self buffs
        if (config && config.self_buffs) {
            let selfRealtimeModifiers = {};
            config.self_buffs.forEach(buff => {
                if (buff.cinema_req && member.cinema < buff.cinema_req) return;
                if (activeBuffsState[buff.id] && buff.dynamic_modifier) {
                    selfRealtimeModifiers[buff.dynamic_modifier.target_buff_id] = buff.dynamic_modifier;
                }
            });

            config.self_buffs.forEach(buff => {
                if (buff.cinema_req && member.cinema < buff.cinema_req) return;
                if (activeBuffsState[buff.id]) {
                    if (buff.dynamic_stat && buff.dynamic_stat.based_on.endsWith("_realtime")) {
                        const modifier = selfRealtimeModifiers[buff.id] || null;
                        applyRealtimeBuffEffect(stats, buff, modifier, pass1Stats[idx]);
                    }
                }
            });
        }

        // H2. Apply realtime team buffs from teammates
        squad.forEach((teammate, tIdx) => {
            if (!teammate) return;
            const tCharId = teammate.characterId;
            const teammateConfig = CHAR_BUFFS_CONFIG[tCharId];
            if (!teammateConfig || !teammateConfig.team_buffs) return;

            let activeModifiers = {};
            teammateConfig.team_buffs.forEach(buff => {
                if (buff.cinema_req && teammate.cinema < buff.cinema_req) return;
                if (activeBuffsState[buff.id] && buff.dynamic_modifier) {
                    activeModifiers[buff.dynamic_modifier.target_buff_id] = buff.dynamic_modifier;
                }
            });

            teammateConfig.team_buffs.forEach(buff => {
                if (buff.cinema_req && teammate.cinema < buff.cinema_req) return;
                if (activeBuffsState[buff.id]) {
                    if (buff.dynamic_stat && buff.dynamic_stat.based_on.endsWith("_realtime")) {
                        const modifier = activeModifiers[buff.id] || null;
                        applyRealtimeBuffEffect(stats, buff, modifier, pass1Stats[tIdx]);
                    }
                }
            });
        });

        return stats;
    });

    return { pass1Stats, pass2Stats };
}

function toWebPanelStats(stats) {
    return {
        hp: stats.hp || 0,
        atk: stats.atk || 0,
        def: stats.def || 0,
        impact: stats.impact || 0,
        critRate: stats.crit_rate || 0,
        critDmg: stats.crit_dmg || 0,
        anomalyMastery: stats.anomaly_mastery || 0,
        anomalyProficiency: stats.anomaly_proficiency || 0,
        penRate: stats.pen_rate || 0,
        penFlat: stats.pen_flat || 0,
        energyRegen: (stats.sp_recovery || 1.2) * ((stats.energy_regen || 100) / 100),
        physicalDmgBonus: stats.element === "物理" ? (stats.attribute_dmg || 0) : 0,
        fireDmgBonus: stats.element === "火属性" ? (stats.attribute_dmg || 0) : 0,
        iceDmgBonus: stats.element === "冰属性" ? (stats.attribute_dmg || 0) : 0,
        electricDmgBonus: stats.element === "电属性" ? (stats.attribute_dmg || 0) : 0,
        etherDmgBonus: stats.element === "以太" ? (stats.attribute_dmg || 0) : 0,
    };
}

function getDriveDiscSetCounts(member) {
    const counts = {};
    (member.driveDiscs || []).forEach((disc) => {
        if (disc.setId) counts[disc.setId] = (counts[disc.setId] || 0) + 1;
    });
    return counts;
}

function buildWebTeamState(pass1Stats, activeChar) {
    const engine = globalThis.ZZZ_NEW_ENGINE;
    if (!engine || typeof engine.resolveWebTeamState !== "function" || !activeChar) {
        return null;
    }

    const team = squad.map((member, index) => {
        if (!member) return null;
        const charData = DB.characters[member.characterId];
        const legacyPanel = pass1Stats[index];
        if (!charData || !legacyPanel) return null;
        return {
            id: member.characterId,
            name: charData.name,
            role: charData.specialty || "",
            element: charData.element || "",
            camp: CHARACTER_FACTIONS_MAP[member.characterId] || "无",
            level: member.level || 60,
            cinema: member.cinema || 0,
            coreLevel: member.coreRank || 0,
            weaponId: member.weaponId || undefined,
            weaponRefinement: member.weaponRefinement || 1,
            driveDiscSetCounts: getDriveDiscSetCounts(member),
            panel: toWebPanelStats(legacyPanel),
        };
    }).filter(Boolean);

    try {
        return engine.resolveWebTeamState({
            attackerId: activeChar.characterId,
            team,
            // 当前计算器是满拐静态结算；甜蜜惊吓是柚叶1画减抗的作用状态。
            enemyStates: { "sweet-frightened": true, stunned: stunnedState },
            assumeFullBuffs: true,
        });
    } catch (error) {
        console.warn("新版队伍 Buff 桥接失败，将继续使用旧版面板：", error);
        return null;
    }
}

function mergeWebPanelIntoLegacyStats(legacyStats, panel) {
    if (!legacyStats || !panel) return legacyStats;
    const elementDamageByName = {
        "物理": panel.physicalDmgBonus,
        "火属性": panel.fireDmgBonus,
        "冰属性": panel.iceDmgBonus,
        "电属性": panel.electricDmgBonus,
        "以太": panel.etherDmgBonus,
        "风属性": panel.windDmgBonus,
    };
    return {
        ...legacyStats,
        hp: panel.hp,
        atk: panel.atk,
        def: panel.def,
        impact: panel.impact,
        crit_rate: panel.critRate,
        crit_dmg: panel.critDmg,
        anomaly_mastery: panel.anomalyMastery,
        anomaly_proficiency: panel.anomalyProficiency,
        pen_rate: panel.penRate,
        pen_flat: panel.penFlat,
        sp_recovery: panel.energyRegen,
        energy_regen: 100,
        // 旧版 pass2 曾把普通增伤写进 attribute_dmg；新版规则中普通增伤
        // 与元素面板是两个区，整合面板必须以新版元素面板覆盖旧值。
        attribute_dmg: Number(elementDamageByName[legacyStats.element]) || 0,
    };
}

function applyBuffEffect(stats, buff, providerPass1Stats, modifier = null) {
    if (buff.dynamic_stat && buff.dynamic_stat.based_on.endsWith("_realtime")) {
        return;
    }

    // 1. Dynamic Attribute Linked support buff
    if (buff.dynamic_stat) {
        if (providerPass1Stats) {
            let baseVal = 0;
            if (buff.dynamic_stat.based_on === "base_atk") {
                baseVal = providerPass1Stats.baseAtk || 0;
            } else {
                baseVal = providerPass1Stats[buff.dynamic_stat.based_on] || 0;
            }

            if (buff.dynamic_stat.offset) {
                baseVal = Math.max(0, baseVal - buff.dynamic_stat.offset);
            }

            // Apply modifiers if present
            let scale = buff.dynamic_stat.scale;
            let cap = buff.dynamic_stat.cap;
            
            if (modifier) {
                if (modifier.scale_add !== undefined) {
                    scale += modifier.scale_add;
                }
                if (modifier.scale_multiplier !== undefined) {
                    scale *= modifier.scale_multiplier;
                    if (cap !== undefined) {
                        cap *= modifier.scale_multiplier;
                    }
                }
                if (modifier.cap_add !== undefined && cap !== undefined) {
                    cap += modifier.cap_add;
                }
            }

            let val = baseVal * scale;
            if (buff.dynamic_stat.flat) {
                val += buff.dynamic_stat.flat;
            }
            if (cap !== undefined) {
                val = Math.min(cap, val);
            }

            const target = buff.dynamic_stat.stat_to_add;
            if (target === "pen_rate") {
                stats.pen_rate += val;
            } else if (target === "atk_flat") {
                stats.combatAtkFlatIn += val;
            } else if (target === "crit_rate") {
                stats.crit_rate += val;
            } else if (target === "crit_dmg") {
                stats.crit_dmg += val;
            } else if (target === "def_flat") {
                stats.combatDefFlatIn += val;
            } else if (target === "attribute_dmg" || target === "dmg_bonus") {
                stats.attribute_dmg += val;
            } else if (target === "daze_bonus") {
                stats.daze_bonus += val;
            } else if (target === "pen_flat") {
                if (stats.breach_power !== undefined) {
                    stats.breach_power += val;
                } else {
                    stats.pen_flat += val;
                }
            } else if (target === "pen_dmg_bonus") {
                stats.pen_dmg_bonus = (stats.pen_dmg_bonus || 0) + val;
            } else if (target === "shield_flat") {
                stats.shield_flat = (stats.shield_flat || 0) + val;
            } else if (target === "def_shred") {
                stats.def_shred += val;
            } else if (target === "anomaly_proficiency") {
                stats.anomaly_proficiency += val;
            } else if (target === "impact") {
                stats.combatImpactPctIn += val;
            }
        }
    }

    // 2. Static buffs
    if (buff.def_shred) {
        stats.def_shred += buff.def_shred;
    }
    if (buff.def_ignore) {
        if (buff.tags && buff.tags.length > 0) {
            stats.tagged_ignore_def_bonuses.push({
                tags: buff.tags,
                value: buff.def_ignore
            });
        } else {
            stats.ignore_def += buff.def_ignore;
        }
    }
    if (buff.res_shred) {
        stats.res_shred += buff.res_shred;
    }
    if (buff.atk_flat) {
        stats.combatAtkFlatIn += buff.atk_flat;
    }
    if (buff.atk_pct) {
        stats.combatAtkPctIn += buff.atk_pct;
    }
    if (buff.crit_rate) {
        stats.crit_rate += buff.crit_rate;
    }
    if (buff.crit_dmg) {
        stats.crit_dmg += buff.crit_dmg;
    }
    if (buff.pen_rate) {
        stats.pen_rate += buff.pen_rate;
    }
    if (buff.pen_flat) {
        if (stats.breach_power !== undefined) {
            stats.breach_power += buff.pen_flat;
        } else {
            stats.pen_flat += buff.pen_flat;
        }
    }
    if (buff.pen_dmg_bonus) {
        stats.pen_dmg_bonus = (stats.pen_dmg_bonus || 0) + buff.pen_dmg_bonus;
    }
    if (buff.anomaly_proficiency) {
        stats.anomaly_proficiency += buff.anomaly_proficiency;
    }
    if (buff.anomaly_mastery) {
        stats.anomaly_mastery = (stats.anomaly_mastery || 0) + buff.anomaly_mastery;
    }
    if (buff.energy_regen) {
        stats.energy_regen = (stats.energy_regen || 0) + buff.energy_regen;
    }
    if (buff.shield_flat) {
        stats.shield_flat = (stats.shield_flat || 0) + buff.shield_flat;
    }
    if (buff.def_flat) {
        stats.combatDefFlatIn += buff.def_flat;
    }
    if (buff.def_pct) {
        stats.combatDefPctIn += buff.def_pct;
    }
    if (buff.hp_flat) {
        stats.combatHpFlatIn += buff.hp_flat;
    }
    if (buff.hp_pct) {
        stats.combatHpPctIn += buff.hp_pct;
    }
    if (buff.impact) {
        stats.combatImpactPctIn += buff.impact;
    }

    if (buff.daze_bonus) {
        if (buff.tags && buff.tags.length > 0) {
            stats.tagged_daze_bonuses.push({
                tags: buff.tags,
                value: buff.daze_bonus
            });
        } else {
            stats.daze_bonus += buff.daze_bonus;
        }
    }

    // 正确的 dmg_bonus 解析逻辑 (专门针对 applyBuffEffect)
    if (buff.dmg_bonus) {
        if (buff.tags && buff.tags.length > 0) {
            // 兼容旧的 anomaly 标签
            if (buff.tags.includes("anomaly")) {
                stats.pure_anomaly_dmg_bonus = (stats.pure_anomaly_dmg_bonus || 0) + buff.dmg_bonus;
                stats.disorder_dmg_bonus = (stats.disorder_dmg_bonus || 0) + buff.dmg_bonus;
            }
            // 新增的独立标签
            if (buff.tags.includes("pure_anomaly")) {
                stats.pure_anomaly_dmg_bonus = (stats.pure_anomaly_dmg_bonus || 0) + buff.dmg_bonus;
            }
            if (buff.tags.includes("disorder")) {
                stats.disorder_dmg_bonus = (stats.disorder_dmg_bonus || 0) + buff.dmg_bonus;
            }
            
            stats.tagged_dmg_bonuses.push({
                tags: buff.tags,
                value: buff.dmg_bonus
            });
        } else {
            stats.attribute_dmg += buff.dmg_bonus;
        }
    }

    if (buff.disorder_ratio_bonus) {
        stats.disorder_ratio_bonus += buff.disorder_ratio_bonus;
    }

    if (buff.additional_multiplier) {
        stats.additional_multipliers.push({
            tags: buff.tags || [],
            value: buff.additional_multiplier
        });
    }

    if (buff.multiplier_ratio) {
        stats.multiplier_ratios.push({
            tags: buff.tags || [],
            value: buff.multiplier_ratio
        });
    }
}

function applyRealtimeBuffEffect(stats, buff, modifier, providerStats = null) {
    if (buff.dynamic_stat) {
        let baseVal = 0;
        const basedOn = buff.dynamic_stat.based_on;
        const src = providerStats || stats;
        if (basedOn === "hp_realtime") {
            baseVal = src.hp || 0;
        } else if (basedOn === "anomaly_mastery_realtime") {
            baseVal = src.anomaly_mastery || 0;
        } else {
            const cleanStat = basedOn.replace("_realtime", "");
            baseVal = src[cleanStat] || src[basedOn] || 0;
        }

        if (buff.dynamic_stat.offset) {
            baseVal = Math.max(0, baseVal - buff.dynamic_stat.offset);
        }

        // Apply modifiers if present
        let scale = buff.dynamic_stat.scale;
        let cap = buff.dynamic_stat.cap;
        
        if (modifier && typeof modifier === "object") {
            if (modifier.scale_add !== undefined) {
                scale += modifier.scale_add;
            }
            if (modifier.scale_multiplier !== undefined) {
                scale *= modifier.scale_multiplier;
                if (cap !== undefined) {
                    cap *= modifier.scale_multiplier;
                }
            }
            if (modifier.cap_add !== undefined && cap !== undefined) {
                cap += modifier.cap_add;
            }
        }

        let val = baseVal * scale;
        if (buff.dynamic_stat.flat) {
            val += buff.dynamic_stat.flat;
        }
        if (cap !== undefined) {
            val = Math.min(cap, val);
        }
        
        // Backwards compatibility for numeric modifier multipliers
        if (modifier && typeof modifier === "number") {
            val *= modifier;
        }

        const target = buff.dynamic_stat.stat_to_add;
        if (target === "pen_flat") {
            stats.pen_flat += val;
        } else if (target === "anomaly_buffs") {
            stats.pure_anomaly_dmg_bonus = (stats.pure_anomaly_dmg_bonus || 0) + val * 100;
            stats.disorder_dmg_bonus = (stats.disorder_dmg_bonus || 0) + val * 100;
        } else if (target === "pen_dmg_bonus") {
            stats.pen_dmg_bonus = (stats.pen_dmg_bonus || 0) + val;
        } else if (target === "crit_rate") {
            stats.crit_rate += val;
        } else if (target === "crit_dmg") {
            stats.crit_dmg += val;
        } else if (target === "dmg_bonus" || target === "attribute_dmg") {
            stats.attribute_dmg += val;
        } else if (target === "anomaly_proficiency") {
            stats.anomaly_proficiency += val;
        }
    }
}

function renderGlobalSubstatsAllocator(activeChar) {
    const container = document.getElementById("global-substats-grid-container");
    const sumSpan = document.getElementById("allocated-rolls-sum");
    if (!container || !sumSpan) return;

    if (!activeChar.globalSubStats) {
        activeChar.globalSubStats = {
            atk_pct: 0, crit_rate: 0, crit_dmg: 0, anomaly_prof: 0, pen_flat: 0,
            atk_flat: 0, hp_pct: 0, def_pct: 0, def_flat: 0, hp_flat: 0
        };
    }

    const keys = ["atk_pct", "crit_rate", "crit_dmg", "anomaly_prof", "pen_flat", "atk_flat", "hp_pct", "def_pct", "def_flat", "hp_flat"];
    const sum = keys.reduce((acc, k) => acc + (activeChar.globalSubStats[k] || 0), 0);
    sumSpan.textContent = sum;

    container.innerHTML = "";
    keys.forEach(k => {
        const item = document.createElement("div");
        item.className = "global-substat-item";
        
        const label = SUBSTAT_LABELS[k] ? SUBSTAT_LABELS[k].split(" (+")[0] : k;
        const rolls = activeChar.globalSubStats[k] || 0;

        item.innerHTML = `
            <div class="global-substat-label">${label}</div>
            <div class="global-substat-val-wrapper">
                <button class="spinner-btn minus" ${rolls <= 0 ? 'disabled' : ''}>-</button>
                <span class="global-substat-value-badge">${rolls}</span>
                <button class="spinner-btn plus" ${sum >= 54 ? 'disabled' : ''}>+</button>
            </div>
        `;

        item.querySelector(".minus").addEventListener("click", () => {
            if (activeChar.globalSubStats[k] > 0) {
                activeChar.globalSubStats[k]--;
                updateUI();
            }
        });

        item.querySelector(".plus").addEventListener("click", () => {
            const currentSum = keys.reduce((acc, x) => acc + (activeChar.globalSubStats[x] || 0), 0);
            if (currentSum < 54) {
                activeChar.globalSubStats[k] = (activeChar.globalSubStats[k] || 0) + 1;
                updateUI();
            }
        });

        container.appendChild(item);
    });
}

// A helper to generate high fidelity dynamic badges
function getDynamicBuffBadgeHtml(buff, providerPass1, labelPrefix = "自身", providerPass2 = null) {
    if (!buff.dynamic_stat || !providerPass1) return "";

    let baseVal = 0;
    let statLabel = "";
    const basedOn = buff.dynamic_stat.based_on;

    if (basedOn.endsWith("_realtime")) {
        const actualStat = basedOn.replace("_realtime", "");
        if (providerPass2) {
            baseVal = providerPass2[actualStat] || 0;
        } else {
            baseVal = providerPass1[actualStat] || 0;
        }
        if (actualStat === "hp") statLabel = "实时生命";
        else if (actualStat === "anomaly_mastery") statLabel = "实时掌控";
        else statLabel = "实时" + actualStat;
    } else if (basedOn === "base_atk") {
        baseVal = providerPass1.baseAtk || 0;
        statLabel = "基础攻击";
    } else {
        baseVal = providerPass1[basedOn] || 0;
        if (basedOn === "atk") statLabel = "面板攻击";
        else if (basedOn === "def") statLabel = "面板防御";
        else if (basedOn === "pen_rate") statLabel = "穿透率";
        else if (basedOn === "impact") statLabel = "冲击力";
        else if (basedOn === "hp") statLabel = "生命值";
        else if (basedOn === "anomaly_mastery") statLabel = "异常掌控";
        else if (basedOn === "energy_regen") statLabel = "能量自动回复";
        else statLabel = basedOn;
    }

    let calculatedVal = baseVal;
    if (buff.dynamic_stat.offset) {
        calculatedVal = Math.max(0, calculatedVal - buff.dynamic_stat.offset);
    }

    let val = calculatedVal * buff.dynamic_stat.scale;
    if (buff.dynamic_stat.flat) {
        val += buff.dynamic_stat.flat;
    }
    if (buff.dynamic_stat.cap !== undefined) {
        val = Math.min(buff.dynamic_stat.cap, val);
    }

    // Determine target label
    const target = buff.dynamic_stat.stat_to_add;
    const targetLabelMap = {
        "pen_rate": "穿透率",
        "pen_flat": "穿透值",
        "crit_rate": "暴击率",
        "crit_dmg": "暴击伤害",
        "def_flat": "防御力",
        "atk_flat": "攻击力",
        "attribute_dmg": "伤害加成",
        "dmg_bonus": "伤害加成",
        "daze_bonus": "失衡值提升",
        "shield_flat": "护盾值",
        "def_shred": "无视防御",
        "anomaly_proficiency": "异常精通",
        "impact": "冲击力",
        "anomaly_buffs": "属性异常增伤"
    };
    const targetLabel = targetLabelMap[target] || target;

    // Format target value
    const percentageTargets = ["pen_rate", "crit_rate", "crit_dmg", "attribute_dmg", "dmg_bonus", "daze_bonus", "def_shred", "impact", "anomaly_buffs"];
    const displayVal = target === "anomaly_buffs" ? val * 100 : val;
    const valText = percentageTargets.includes(target) ? `${displayVal.toFixed(1)}%` : displayVal.toFixed(0);

    // Format source base value
    const percentageSources = ["pen_rate", "crit_rate", "crit_dmg", "energy_regen"];
    const baseValText = percentageSources.includes(basedOn) ? `${baseVal.toFixed(1)}%` : baseVal.toFixed(0);

    return `<div class="buff-badge-dynamic">数据联动：${labelPrefix}的${statLabel} (${baseValText}) ➜ ${labelPrefix === "自身" ? "自身" : "全队"} +${valText} ${targetLabel}</div>`;
}

// 新增一个工具函数，用于将数组解包为当前精炼等级的数值
function resolveWeaponBuff(baseBuff, refinementLevel) {
    const refineIndex = (refinementLevel || 1) - 1; // 1阶对应索引 0，5阶对应索引 4
    let buff = JSON.parse(JSON.stringify(baseBuff)); // 深拷贝，防止污染原字典
    
    // 遍历解析第一层静态属性 (如 crit_rate, dmg_bonus)
    Object.keys(buff).forEach(key => {
        if (Array.isArray(buff[key])) {
            buff[key] = buff[key][refineIndex];
        }
    });
    
    // 如果有动态转化属性 (dynamic_stat)，一并解析
    if (buff.dynamic_stat) {
        Object.keys(buff.dynamic_stat).forEach(key => {
            if (Array.isArray(buff.dynamic_stat[key])) {
                buff.dynamic_stat[key] = buff.dynamic_stat[key][refineIndex];
            }
        });
    }
    
    // 修改名称，方便在面板上直观看到当前阶数
    buff.name = `${buff.name} <span class="badge badge-rarity" style="font-size:0.5rem">精${refinementLevel}</span>`;
    return buff;
}

function renderSquadBuffsPanel(activeChar, pass2Stats = null) {
    const container = document.getElementById("squad-buffs-container-row");
    if (!container) return;

    container.innerHTML = "";

    const selfCol = document.createElement("div");
    selfCol.className = "buff-column";
    selfCol.innerHTML = `<div class="buff-column-title">当前操作角色自适增益 / ACTIVE SELF BUFFS</div>`;

    const teamCol = document.createElement("div");
    teamCol.className = "buff-column";
    teamCol.innerHTML = `<div class="buff-column-title">小队队友辅助 / TEAMMATE BUFFS</div>`;

    // 2. Get Pass 1 stats to calculate dynamic badges
    const pass1Stats = squad.map(member => {
        if (!member) return null;
        return calculateFinalStatsPass1(member);
    });

    const activeCharId = activeChar.characterId;
    const activeCharData = DB.characters[activeCharId];
    const activeConfig = CHAR_BUFFS_CONFIG[activeCharId];
    let hasSelfBuffs = false;

    // Helper to render a buff card
    function renderBuffCard(col, buff, isTeamBuff, providerName = "", providerPass1 = null, borderLime = false, providerMember = null) {
        const isExtra = buff.name.includes("额外能力") || buff.id.includes("extra");
        let extraActive = true;
        if (isExtra && providerMember) {
            extraActive = isSquadActiveExtraAbility(providerMember, squad);
            activeBuffsState[buff.id] = extraActive;
        }

        if (activeBuffsState[buff.id] === undefined) {
            activeBuffsState[buff.id] = buff.active !== false;
        }

        const isChecked = activeBuffsState[buff.id] ? "checked" : "";
        const isDisabled = (isExtra && !extraActive) ? "disabled" : "";
        const card = document.createElement("div");
        card.className = "buff-item-card";
        if (borderLime) {
            card.style.borderLeft = "3px solid var(--clr-lime, #2BAD00)";
        }

        let badgeHtml = "";
        if (buff.dynamic_stat) {
            const providerIdx = isTeamBuff && providerName ? squad.findIndex(s => s && DB.characters[s.characterId] && DB.characters[s.characterId].name === providerName) : activeSlotIndex;
            const providerPass2 = pass2Stats && providerIdx !== -1 ? pass2Stats[providerIdx] : null;
            badgeHtml = getDynamicBuffBadgeHtml(buff, providerPass1, providerName || "自身", providerPass2);
        }

        let extraBadge = "";
        if (isExtra) {
            if (extraActive) {
                extraBadge = `<span class="badge" style="font-size: 0.55rem; background: rgba(43,173,0,0.15); color: var(--clr-lime, #2BAD00); border-color: rgba(43,173,0,0.3); margin-left: 0.25rem;">🟢 核心已激活</span>`;
            } else {
                extraBadge = `<span class="badge" style="font-size: 0.55rem; background: rgba(239,68,68,0.15); color: var(--clr-red, #EF4444); border-color: rgba(239,68,68,0.3); margin-left: 0.25rem;">🔴 条件未达成</span>`;
            }
        }

        card.innerHTML = `
            <div class="buff-checkbox-wrapper">
                <input type="checkbox" id="chk-buff-${buff.id}" class="buff-checkbox" ${isChecked} ${isDisabled}>
            </div>
            <div class="buff-meta">
                <div class="flex justify-between items-center" style="display: flex; justify-content: space-between; align-items: center;">
                    <label for="chk-buff-${buff.id}" class="buff-name cursor-pointer flex items-center gap-1" style="display: flex; align-items: center; gap: 4px;">
                        ${buff.name}
                        ${extraBadge}
                    </label>
                    ${isTeamBuff && providerName ? `<span class="badge" style="font-size: 0.55rem; background: rgba(168,85,247,0.12); color: var(--clr-purple); border-color: rgba(168,85,247,0.25);">${providerName}</span>` : ""}
                </div>
                <p class="buff-desc" style="margin-top: 4px; margin-bottom: 4px;">${buff.desc}</p>
                ${badgeHtml}
            </div>
        `;

        card.querySelector("input").addEventListener("change", (e) => {
            activeBuffsState[buff.id] = e.target.checked;
            updateUI();
        });

        col.appendChild(card);
    }

    // A1. Render Configured Self Buffs
    if (activeConfig && activeConfig.self_buffs) {
        activeConfig.self_buffs.forEach(buff => {
            // Skip cinema-gated buffs if cinema level is insufficient
            if (buff.cinema_req && activeChar.cinema < buff.cinema_req) return;
            hasSelfBuffs = true;
            const activePass1 = pass1Stats[activeSlotIndex];
            renderBuffCard(selfCol, buff, false, "自身", activePass1, false, activeChar);
        });
    }

    // A1.5. Render Active Character's own Team Buffs
    if (activeConfig && activeConfig.team_buffs) {
        activeConfig.team_buffs.forEach(buff => {
            // Skip cinema-gated buffs if cinema level is insufficient
            if (buff.cinema_req && activeChar.cinema < buff.cinema_req) return;
            hasSelfBuffs = true;
            const activePass1 = pass1Stats[activeSlotIndex];
            renderBuffCard(selfCol, buff, false, "自身(全队)", activePass1, false, activeChar);
        });
    }

    // A2. Render Active Character's 4pc set self-buffs
    const activeSetCounts = {};
    activeChar.driveDiscs.forEach(disc => {
        if (disc.setId) {
            activeSetCounts[disc.setId] = (activeSetCounts[disc.setId] || 0) + 1;
        }
    });

    Object.keys(activeSetCounts).forEach(setId => {
        const count = activeSetCounts[setId];
        if (count >= 4) {
            const buffs = getSet4PcBuffs(setId, activeCharData.specialty);
            if (buffs.self && Object.keys(buffs.self).length > 0) {
                hasSelfBuffs = true;
                const setMeta = DB.driveDiscs.sets[setId];
                const setName = setMeta ? setMeta.name : setId;
                const setDesc = setMeta ? (setMeta.desc4 || setMeta.desc_4pc || "4件套效果") : "4件套效果";
                const buffId = `4pc-${activeCharId}-${setId}`;
                const buff = {
                    id: buffId,
                    name: `${setName} 4件套`,
                    desc: setDesc,
                    active: true
                };
                renderBuffCard(selfCol, buff, false, "自身", null);
            }
        }
    });

    // A3. Render Active Character's Weapon Buffs
    const weaponId = activeChar.weaponId;
    const weaponConfig = WEAPON_BUFFS_CONFIG[weaponId];
    if (weaponConfig && weaponConfig.self_buffs) {
        weaponConfig.self_buffs.forEach(baseBuff => {
            hasSelfBuffs = true;
            const currentBuff = resolveWeaponBuff(baseBuff, activeChar.weaponRefinement);
            renderBuffCard(selfCol, currentBuff, false, "音擎特效", pass1Stats[activeSlotIndex], true);
        });
    }
    
    // (同理，如果你配置了武器的 team_buffs，也在队友遍历的循环里加一段类似的解析并挂载到 teamCol 即可)

    if (!hasSelfBuffs) {
        const emptyMsg = document.createElement("div");
        emptyMsg.className = "text-xs text-slate-500 text-center py-4";
        emptyMsg.textContent = "当前主控角色无特殊自拐被动";
        selfCol.appendChild(emptyMsg);
    }

    // B. Render Teammate Support Buffs
    let hasTeamBuffs = false;

    squad.forEach((member, tIdx) => {
        if (!member || tIdx === activeSlotIndex) return;

        const teammateId = member.characterId;
        const teammateData = DB.characters[teammateId];
        const teammateConfig = CHAR_BUFFS_CONFIG[teammateId];
        if (!teammateData) return;

        const providerPass1 = pass1Stats[tIdx];

        // B1. Configured team buffs
        if (teammateConfig && teammateConfig.team_buffs) {
            teammateConfig.team_buffs.forEach(buff => {
                // Skip cinema-gated buffs if teammate cinema level is insufficient
                if (buff.cinema_req && member.cinema < buff.cinema_req) return;
                hasTeamBuffs = true;
                renderBuffCard(teamCol, buff, true, teammateData.name, providerPass1, false, member);
            });
        }

        // B2. Teammate's 4pc set team buffs
        const tSetCounts = {};
        member.driveDiscs.forEach(disc => {
            if (disc.setId) {
                tSetCounts[disc.setId] = (tSetCounts[disc.setId] || 0) + 1;
            }
        });

        Object.keys(tSetCounts).forEach(setId => {
            const count = tSetCounts[setId];
            if (count >= 4) {
                const buffs = getSet4PcBuffs(setId, teammateData.specialty);
                if (buffs.team && Object.keys(buffs.team).length > 0) {
                    hasTeamBuffs = true;
                    const setMeta = DB.driveDiscs.sets[setId];
                    const setName = setMeta ? setMeta.name : setId;
                    const setDesc = setMeta ? (setMeta.desc4 || setMeta.desc_4pc || "4件套全队辅助效果") : "4件套全队辅助效果";
                    const buffId = `4pc-${teammateId}-${setId}`;
                    const buff = {
                        id: buffId,
                        name: `${setName} 4件套`,
                        desc: setDesc,
                        active: true
                    };
                    renderBuffCard(teamCol, buff, true, teammateData.name, null);
                }
            }
        });

    });

    if (!hasTeamBuffs) {
        const emptyMsg = document.createElement("div");
        emptyMsg.className = "text-xs text-slate-500 text-center py-4";
        emptyMsg.textContent = "小队中无其他队友或队友无辅助被动";
        teamCol.appendChild(emptyMsg);
    }

    container.appendChild(selfCol);
    container.appendChild(teamCol);
}

function parseWeaponPassive(desc) {
    const buffs = { dmg_bonus: 0, atk_pct: 0, crit_rate: 0, crit_dmg: 0, pen_rate: 0 };
    if (!desc) return buffs;

    // Clean html tags first
    const cleanDesc = desc.replace(/<[^>]+>/g, '');

    // Common ZZZ W-Engine patterns
    const regexDmg = /(?:伤害|普通攻击伤害|特殊技伤害|连携技伤害|终结技伤害)提升(?:了)?(\d+(?:\.\d+)?)%/;
    const regexAtk = /攻击力提升(?:了)?(\d+(?:\.\d+)?)%/;
    const regexCrit = /暴击率提升(?:了)?(\d+(?:\.\d+)?)%/;
    const regexCritDmg = /暴击伤害提升(?:了)?(\d+(?:\.\d+)?)%/;
    const regexPen = /(?:穿透率|无视防御)提升(?:了)?(\d+(?:\.\d+)?)%/;

    let m;
    if ((m = cleanDesc.match(regexDmg))) buffs.dmg_bonus = parseFloat(m[1]);
    if ((m = cleanDesc.match(regexAtk))) buffs.atk_pct = parseFloat(m[1]);
    if ((m = cleanDesc.match(regexCrit))) buffs.crit_rate = parseFloat(m[1]);
    if ((m = cleanDesc.match(regexCritDmg))) buffs.crit_dmg = parseFloat(m[1]);
    if ((m = cleanDesc.match(regexPen))) buffs.pen_rate = parseFloat(m[1]);

    return buffs;
}

function getSet2PcBonus(setId, charElement) {
    const statBonus = {};
    if (!setId) return statBonus;
    
    switch (setId) {
        case "31000": statBonus.crit_rate = 8.0; break;
        case "31100": statBonus.pen_rate = 8.0; break;
        case "31200": statBonus.impact = 6.0; break;
        case "31300": statBonus.anomaly_proficiency = 30; break;
        case "31400": statBonus.atk_pct = 10.0; break;
        case "31500": statBonus.def_pct = 16.0; break;
        case "31600": statBonus.energy_regen = 20.0; break;
        case "31800": statBonus.anomaly_proficiency = 30; break;
        case "32200": if (charElement === "火属性") statBonus.attribute_dmg = 10.0; break;
        case "32300": if (charElement === "以太") statBonus.attribute_dmg = 10.0; break;
        case "32400": if (charElement === "电属性") statBonus.attribute_dmg = 10.0; break;
        case "32500": if (charElement === "冰属性") statBonus.attribute_dmg = 10.0; break;
        case "32600": if (charElement === "物理") statBonus.attribute_dmg = 10.0; break;
        case "32700": statBonus.crit_dmg = 16.0; break;
        case "32800": statBonus.atk_pct = 10.0; break;
        case "33000": statBonus.anomaly_mastery = 8.0; break;
        case "33100": statBonus.hp_pct = 10.0; break;
        case "33200": statBonus.daze_bonus = 6.0; break;
        case "33400": statBonus.energy_regen = 20.0; break;
        case "33500": if (charElement === "物理") statBonus.attribute_dmg = 10.0; break;
        case "33600": if (charElement === "以太") statBonus.attribute_dmg = 10.0; break;
        case "33700": statBonus.hp_pct = 10.0; break;
        case "33800": if (charElement === "冰属性") statBonus.attribute_dmg = 10.0; break;
        case "33900": if (charElement === "风属性") statBonus.attribute_dmg = 10.0; break;
        case "34000": if (charElement === "以太") statBonus.attribute_dmg = 10.0; break;
    }
    return statBonus;
}

function renderActiveSetsStatus(descriptions) {
    const list = document.getElementById("sets-active-status");
    if (!list) return;

    if (descriptions.length === 0) {
        list.innerHTML = `<div class="text-sm text-slate-400">未激活任何套装效果</div>`;
        return;
    }

    list.innerHTML = "";
    descriptions.forEach(set => {
        const badge = document.createElement("div");
        badge.className = "set-active-badge flex-col gap-1";
        badge.innerHTML = `
            <div class="flex items-center justify-between">
                <span class="set-active-title font-semibold">${set.name}</span>
                <span class="badge badge-rarity" style="font-size: 0.55rem;">${set.type}</span>
            </div>
            <p class="set-active-desc">${formatHtmlColors(set.desc)}</p>
        `;
        list.appendChild(badge);
    });
}

function getElementDamageKey(element) {
    const keys = {
        "物理": "physical",
        "火属性": "fire",
        "冰属性": "ice",
        "电属性": "electric",
        "以太": "ether",
        "风属性": "wind",
    };
    return keys[element] || "physical";
}

function getSelectedCrisisBuffEffects() {
    return getAllCrisisBuffs()
        .filter((buff) => selectedCrisisBuffs.has(buff.id))
        .map((buff) => {
            const cleanText = String(buff.desc || "").replace(/<[^>]+>/g, "");
            const damageMatch = cleanText.match(/造成的伤害提升(\d+(?:\.\d+)?)%/);
            const attackMatch = cleanText.match(/攻击力提升(\d+(?:\.\d+)?)%/);
            return {
                id: `crisis:${buff.id}`,
                label: `${buff.title}｜危局增益`,
                damageBonus: damageMatch ? Number(damageMatch[1]) : 0,
                attackPercent: attackMatch ? Number(attackMatch[1]) : 0,
            };
        });
}

function getOutOfCombatDamageBonusSources(member, charData, outStats) {
    const sources = [];
    if (!member || !charData || !outStats) return sources;

    (member.driveDiscs || []).forEach((disc, slotIndex) => {
        const slot = slotIndex + 1;
        if (disc.mainStat !== "属性伤害加成") return;
        const options = DB.driveDiscs.max_level_main_stats?.[`partition_${slot}`]?.options;
        const value = Number.parseFloat(options?.[disc.mainStat]);
        if (!Number.isFinite(value) || value === 0) return;
        sources.push({
            id: `drive-main:${slot}`,
            label: `驱动盘${slot}号位｜属性伤害主词条`,
            value,
        });
    });

    const setCounts = getDriveDiscSetCounts(member);
    Object.entries(setCounts).forEach(([setId, count]) => {
        if (count < 2) return;
        const value = Number(getSet2PcBonus(setId, charData.element).attribute_dmg) || 0;
        if (value === 0) return;
        sources.push({
            id: `drive-set:${setId}:2pc`,
            label: `${DB.driveDiscs.sets?.[setId]?.name || setId}｜2件套`,
            value,
        });
    });

    const traced = sources.reduce((sum, source) => sum + source.value, 0);
    const remainder = (Number(outStats.attribute_dmg) || 0) - traced;
    if (Math.abs(remainder) >= 0.01) {
        sources.push({
            id: "panel:other-attribute-damage",
            label: "其他局外面板属性增伤",
            value: remainder,
        });
    }
    return sources;
}

function groupDamageBonusSources(sources) {
    const grouped = new Map();
    sources.forEach((source) => {
        const key = source.id || source.label;
        const current = grouped.get(key) || { ...source, value: 0 };
        current.value += Number(source.value) || 0;
        grouped.set(key, current);
    });
    return [...grouped.values()].filter((source) => Math.abs(source.value) >= 0.01);
}

function buildCurrentDamageBonusSummary(outStats, teamState) {
    const member = squad[activeSlotIndex];
    const charData = member && DB.characters[member.characterId];
    const webBuffs = teamState && teamState.buffs;
    const webPanel = teamState && teamState.activePanel;
    const skillCategory = activeSkillCategory === "chain" ? "ultimate" : activeSkillCategory;
    const skillLabels = {
        basic: "普通攻击",
        dodge: "闪避",
        assist: "支援技",
        special: "特殊技 / 强化特殊技",
        ultimate: "终结技",
    };
    if (!member || !charData || !webBuffs || !webPanel) {
        const fallback = Number(outStats && outStats.attribute_dmg) || 0;
        return {
            total: fallback,
            context: `${skillLabels[skillCategory] || "当前技能页"}｜旧版回退`,
            sources: fallback === 0 ? [] : [{ id: "legacy:attribute", label: "局外属性伤害加成", value: fallback }],
        };
    }

    const elementKey = getElementDamageKey(charData.element);
    const elementStat = `${elementKey}DmgBonus`;
    const sources = getOutOfCombatDamageBonusSources(member, charData, outStats);
    const elementPanelSources = (webBuffs.combatPanelModifiers || [])
        .filter((modifier) => modifier.stat === elementStat)
        .map((modifier) => ({
            id: modifier.sourceId,
            label: modifier.label,
            value: Number(modifier.value) || 0,
        }));
    sources.push(...elementPanelSources);

    const normalSources = (webBuffs.normalDamageBonusSources || []).map((source) => ({
        id: source.id,
        label: source.label,
        value: Number(source.value) || 0,
    }));
    sources.push(...normalSources);

    const scopedSources = (webBuffs.scopedDamageBonusEffects || [])
        .filter((effect) => webScopeMatches(effect.scope, "direct", skillCategory, elementKey))
        .map((effect) => ({
            id: effect.id,
            label: effect.label,
            value: Number(effect.percent) || 0,
        }));
    sources.push(...scopedSources);

    const crisisSources = getSelectedCrisisBuffEffects()
        .filter((effect) => effect.damageBonus !== 0)
        .map((effect) => ({ id: effect.id, label: effect.label, value: effect.damageBonus }));
    sources.push(...crisisSources);

    const panelBonus = getWebElementDamageBonus(webPanel, elementKey);
    const normalBonus = Number(webBuffs.normalDamageBonusPercent) || 0;
    const scopedBonus = scopedSources.reduce((sum, source) => sum + source.value, 0);
    const crisisBonus = crisisSources.reduce((sum, source) => sum + source.value, 0);
    const total = panelBonus + normalBonus + scopedBonus + crisisBonus;

    const grouped = groupDamageBonusSources(sources);
    const traced = grouped.reduce((sum, source) => sum + source.value, 0);
    const traceDifference = total - traced;
    if (Math.abs(traceDifference) >= 0.01) {
        grouped.push({
            id: "trace:unclassified-damage-bonus",
            label: "其他已计入的规则增伤",
            value: traceDifference,
        });
    }
    return {
        total,
        context: `${skillLabels[skillCategory] || skillCategory}｜${charData.element}`,
        sources: grouped,
    };
}

function renderLivePanelStats(outStats, finalStats, teamState = null) {
    if (!finalStats) finalStats = outStats;

    const panelModifiers = teamState && teamState.buffs && Array.isArray(teamState.buffs.combatPanelModifiers)
        ? teamState.buffs.combatPanelModifiers
        : [];
    const statAliases = {
        hp: ["hp", "hpPct"],
        atk: ["atk", "atkPct"],
        def: ["def", "defPct"],
        impact: ["impact", "impactPct"],
        critRate: ["critRate"],
        critDmg: ["critDmg"],
        penRate: ["penRate"],
        penFlat: ["penFlat"],
        anomalyProficiency: ["anomalyProficiency"],
        anomalyMastery: ["anomalyMastery", "anomalyMasteryPct"],
        energyRegen: ["energyRegen", "energyRegenPct"],
        attributeDmg: ["physicalDmgBonus", "fireDmgBonus", "iceDmgBonus", "electricDmgBonus", "etherDmgBonus", "windDmgBonus"],
    };
    const percentStats = new Set([
        "hpPct", "atkPct", "defPct", "impactPct", "critRate", "critDmg", "penRate",
        "anomalyMasteryPct", "energyRegenPct", "physicalDmgBonus", "fireDmgBonus",
        "iceDmgBonus", "electricDmgBonus", "etherDmgBonus", "windDmgBonus",
    ]);
    const escapeHtml = (value) => String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    const getBreakdown = (displayStat) => {
        const aliases = statAliases[displayStat] || [];
        const grouped = new Map();
        panelModifiers.forEach((modifier) => {
            if (!aliases.includes(modifier.stat)) return;
            const key = `${modifier.sourceId}:${modifier.stat}`;
            const current = grouped.get(key) || { ...modifier, value: 0 };
            current.value += Number(modifier.value) || 0;
            grouped.set(key, current);
        });
        return [...grouped.values()];
    };
    const renderBuffDelta = (diffStr, displayStat) => {
        const breakdown = getBreakdown(displayStat);
        if (breakdown.length === 0) {
            return `<span style="color: var(--clr-green); font-weight: 600;">+ ${diffStr}</span>`;
        }
        const rows = breakdown.map((item) => {
            const value = Number(item.value) || 0;
            const suffix = percentStats.has(item.stat) ? "%" : (item.stat === "energyRegen" ? "/秒" : "");
            const formatted = Number.isInteger(value) ? value.toString() : value.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
            return `<span class="live-stat-tooltip-row"><strong>+${formatted}${suffix}</strong><span>${escapeHtml(item.label)}</span></span>`;
        }).join("");
        return `<span class="live-stat-breakdown" tabindex="0" style="color: var(--clr-green); font-weight: 600;">+ ${diffStr}<span class="live-stat-tooltip" role="tooltip"><span class="live-stat-tooltip-title">局内增量来源</span>${rows}</span></span>`;
    };

    const formatStat = (outVal, finalVal, isPct = false, precision = 1, displayStat = "") => {
        let outStr = isPct ? `${outVal.toFixed(precision)}%` : Math.round(outVal).toString();
        if (Math.abs(outVal - finalVal) < 0.01) {
            return outStr;
        } else {
            const diff = finalVal - outVal;
            if (diff > 0) {
                const diffStr = isPct ? `${diff.toFixed(precision)}%` : Math.round(diff).toString();
                return `${outStr} ${renderBuffDelta(diffStr, displayStat)}`;
            } else {
                const diffStr = isPct ? `${Math.abs(diff).toFixed(precision)}%` : Math.round(Math.abs(diff)).toString();
                return `${outStr} <span style="color: #EF4444; font-weight: 600;">- ${diffStr}</span>`;
            }
        }
    };

    document.getElementById("val-total-hp").innerHTML = formatStat(outStats.hp, finalStats.hp, false, 1, "hp");
    document.getElementById("val-total-atk").innerHTML = formatStat(outStats.atk, finalStats.atk, false, 1, "atk");
    document.getElementById("val-total-def").innerHTML = formatStat(outStats.def, finalStats.def, false, 1, "def");
    document.getElementById("val-total-impact").innerHTML = formatStat(outStats.impact, finalStats.impact, false, 1, "impact");
    document.getElementById("val-total-crit-rate").innerHTML = formatStat(outStats.crit_rate, finalStats.crit_rate, true, 1, "critRate");
    document.getElementById("val-total-crit-dmg").innerHTML = formatStat(outStats.crit_dmg, finalStats.crit_dmg, true, 1, "critDmg");
    document.getElementById("val-total-pen-rate").innerHTML = formatStat(outStats.pen_rate, finalStats.pen_rate, true, 1, "penRate");
    const lblPenFlat = document.querySelector("#val-total-pen-flat") ? document.querySelector("#val-total-pen-flat").previousElementSibling : null;
    if (finalStats.breach_power !== undefined) {
        if (lblPenFlat) lblPenFlat.innerHTML = "贯穿力 (Breach Power)";
        const outBreachPower = 0.3 * outStats.atk + 0.1 * outStats.hp;
        document.getElementById("val-total-pen-flat").innerHTML = formatStat(outBreachPower, finalStats.breach_power, false, 1, "penFlat");
    } else {
        if (lblPenFlat) lblPenFlat.innerHTML = "穿透值 (PEN Flat)";
        document.getElementById("val-total-pen-flat").innerHTML = formatStat(outStats.pen_flat, finalStats.pen_flat, false, 1, "penFlat");
    }
    document.getElementById("val-total-anomaly-proficiency").innerHTML = formatStat(outStats.anomaly_proficiency, finalStats.anomaly_proficiency, false, 1, "anomalyProficiency");
    document.getElementById("val-total-dmg-bonus").innerHTML = formatStat(outStats.attribute_dmg, finalStats.attribute_dmg, true, 1, "attributeDmg");
    document.getElementById("val-total-anomaly-mastery").innerHTML = formatStat(outStats.anomaly_mastery || 0, finalStats.anomaly_mastery || 0, false, 1, "anomalyMastery");

    const formatEnergy = (outVal, finalVal) => {
        let outStr = `${outVal.toFixed(2)}/秒`;
        if (Math.abs(outVal - finalVal) < 0.01) {
            return outStr;
        } else {
            const diff = finalVal - outVal;
            if (diff > 0) {
                return `${outStr} ${renderBuffDelta(`${diff.toFixed(2)}/秒`, "energyRegen")}`;
            } else {
                return `${outStr} <span style="color: #EF4444; font-weight: 600;">- ${Math.abs(diff).toFixed(2)}/秒</span>`;
            }
        }
    };
    const outEnergy = (outStats.sp_recovery || 1.2) * ((outStats.energy_regen || 100) / 100);
    const finalEnergy = (finalStats.sp_recovery || 1.2) * ((finalStats.energy_regen || 100) / 100);
    document.getElementById("val-total-energy-regen").innerHTML = formatEnergy(outEnergy, finalEnergy);

    const totalDamageElement = document.getElementById("val-current-total-dmg-bonus");
    const totalDamageContext = document.getElementById("lbl-total-damage-context");
    if (totalDamageElement) {
        const summary = buildCurrentDamageBonusSummary(outStats, teamState);
        const rows = summary.sources.length > 0
            ? summary.sources.map((source) => {
                const value = Number(source.value) || 0;
                const sign = value >= 0 ? "+" : "";
                const formatted = Number.isInteger(value)
                    ? value.toString()
                    : value.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
                return `<span class="live-stat-tooltip-row"><strong>${sign}${formatted}%</strong><span>${escapeHtml(source.label)}</span></span>`;
            }).join("")
            : `<span class="live-stat-tooltip-row"><span>当前没有生效的增伤来源</span></span>`;
        totalDamageElement.innerHTML = `<span class="live-stat-breakdown" tabindex="0">+${summary.total.toFixed(1)}%<span class="live-stat-tooltip" role="tooltip"><span class="live-stat-tooltip-title">当前招式增伤组成</span>${rows}</span></span>`;
        if (totalDamageContext) totalDamageContext.textContent = summary.context;
    }
}

let bossFieldCritDmgStacks = 0;

const BOSS_FIELD_BUFFS = {
    "太初梦魇": {
        name: "太初梦魇场地环境",
        desc: "首领受到的异常伤害降低30%，当其从[秽盾]状态切换回普通状态，或从普通状态切换为[秽盾]状态时，使代理人对其造成的暴击伤害提升20%，最多叠加3层，当其从失衡状态恢复时层数重置。",
        has_crit_dmg_stacks: true,
        crit_dmg_per_stack: 20, // % 暴伤每层
        max_stacks: 3,
        anomaly_dmg_reduction: 30 // % 异常伤害减免
    }
};

function getAllCrisisBuffs() {
    let allBuffs = [];
    let titleToDescs = {}; // Map of title -> set of descriptions to detect differences
    
    // First pass: collect and find all duplicate titles with different descriptions
    Object.entries(DB.crisisBuffs).forEach(([groupId, group]) => {
        if (!group.stages) return;
        Object.entries(group.stages).forEach(([stageId, stage]) => {
            if (!stage.selectable_buffs) return;
            stage.selectable_buffs.forEach((buff, index) => {
                let title = buff.title || "";
                let desc = buff.desc || "";
                
                // TBD Rename Rule
                if (title.toUpperCase().includes("TBD")) {
                    const phase = groupId.slice(-2);
                    title = `TBD${phase}buff${index + 1}`;
                }
                
                if (!titleToDescs[title]) {
                    titleToDescs[title] = new Set();
                }
                titleToDescs[title].add(desc);
            });
        });
    });
    
    // Second pass: construct final list of buffs with unique displayed titles
    let seenBuffIds = new Set();
    Object.entries(DB.crisisBuffs).forEach(([groupId, group]) => {
        if (!group.stages) return;
        Object.entries(group.stages).forEach(([stageId, stage]) => {
            if (!stage.selectable_buffs) return;
            stage.selectable_buffs.forEach((buff, index) => {
                // Prevent duplicate buff instances in the global selector
                if (seenBuffIds.has(buff.id)) return;
                seenBuffIds.add(buff.id);
                
                let originalTitle = buff.title || "";
                let title = originalTitle;
                let desc = buff.desc || "";
                
                // TBD Rename Rule
                if (title.toUpperCase().includes("TBD")) {
                    const phase = groupId.slice(-2);
                    title = `TBD${phase}buff${index + 1}`;
                }
                
                // Duplicate Title Resolution Rule
                let displayTitle = title;
                if (titleToDescs[title] && titleToDescs[title].size > 1) {
                    displayTitle = `${title} (${groupId}${originalTitle})`;
                }
                
                allBuffs.push({
                    id: buff.id,
                    title: displayTitle,
                    desc: desc,
                    groupId: groupId,
                    stageId: stageId
                });
            });
        });
    });
    
    // Sort buffs so that they look neat (TBD at the end, alphabetically by title)
    allBuffs.sort((a, b) => {
        const aTbd = a.title.toUpperCase().includes("TBD");
        const bTbd = b.title.toUpperCase().includes("TBD");
        if (aTbd && !bTbd) return 1;
        if (!aTbd && bTbd) return -1;
        return a.title.localeCompare(b.title, "zh");
    });
    
    return allBuffs;
}

function renderFieldEnvironment(monster) {
    const container = document.getElementById("field-buffs-container");
    if (!container) return;

    if (!monster) {
        container.innerHTML = `<div class="text-xs text-slate-400">请选择一个首领目标。</div>`;
        return;
    }

    // Find if there is a match in BOSS_FIELD_BUFFS
    let matchedKey = null;
    Object.keys(BOSS_FIELD_BUFFS).forEach(key => {
        if (monster.name.includes(key)) {
            matchedKey = key;
        }
    });

    if (!matchedKey) {
        container.innerHTML = `<div class="text-xs text-slate-400">该首领没有专属战场环境效果。</div>`;
        return;
    }

    const fieldBuff = BOSS_FIELD_BUFFS[matchedKey];
    container.innerHTML = "";

    const card = document.createElement("div");
    card.className = "flex-col gap-2 p-2";
    card.style.background = "rgba(0,0,0,0.2)";
    card.style.borderRadius = "6px";
    card.style.border = "1px solid rgba(255,255,255,0.05)";

    let stacksHtml = "";
    if (fieldBuff.has_crit_dmg_stacks) {
        stacksHtml = `
            <div class="flex items-center justify-between text-xs mt-2 border-t pt-2" style="border-color: rgba(255,255,255,0.05); display: flex;">
                <span class="text-slate-300">秽盾/普通状态切换暴伤层数 (当前: +${bossFieldCritDmgStacks * fieldBuff.crit_dmg_per_stack}%):</span>
                <select id="select-field-crit-dmg-stacks" class="form-select rounded-rect text-right text-xs" style="width: 70px; background: rgba(0,0,0,0.4); color: #fff; padding: 2px;">
                    <option value="0" ${bossFieldCritDmgStacks === 0 ? "selected" : ""}>0 层</option>
                    <option value="1" ${bossFieldCritDmgStacks === 1 ? "selected" : ""}>1 层</option>
                    <option value="2" ${bossFieldCritDmgStacks === 2 ? "selected" : ""}>2 层</option>
                    <option value="3" ${bossFieldCritDmgStacks === 3 ? "selected" : ""}>3 层</option>
                </select>
            </div>
        `;
    }

    card.innerHTML = `
        <div class="flex-col gap-1" style="display: flex;">
            <span class="font-semibold text-xs text-glow" style="color: var(--clr-cyan);">${fieldBuff.name}</span>
            <p class="text-xs text-slate-300" style="margin-top: 2px; line-height: 1.4;">${fieldBuff.desc}</p>
        </div>
        ${stacksHtml}
    `;

    container.appendChild(card);

    // Bind event listener to the stacks dropdown
    const selectStacks = document.getElementById("select-field-crit-dmg-stacks");
    if (selectStacks) {
        selectStacks.addEventListener("change", (e) => {
            bossFieldCritDmgStacks = parseInt(e.target.value) || 0;
            updateUI();
        });
    }
}

// =====================================================================
// 9. STAGE CRISIS & TARGET SIMULATOR UPDATER
// =====================================================================
function updateMonsterSimulator(charStats, teamState = null) {
    const monster = DB.monsters[targetMonsterId];
    if (!monster) return;

    const webBuffs = teamState && teamState.buffs;
    const useWebTeamState = Boolean(webBuffs && teamState.activePanel);
    const activeMember = squad[activeSlotIndex];
    const activeCharacterData = activeMember && DB.characters[activeMember.characterId];
    const previewDamageKind = activeCharacterData?.specialty === "异常" ? "assault" : "direct";
    const previewSkillCategory = activeSkillCategory === "chain" ? "ultimate" : activeSkillCategory;
    const previewElement = getElementDamageKey(charStats.element);

    // Load monster base details
    document.getElementById("lbl-target-boss-name").textContent = monster.name;
    document.getElementById("lbl-target-boss-type").textContent = monster.rarity >= 1 ? "首领级敌人 (BOSS)" : "精英级敌人";
    document.getElementById("img-target-boss").src = monster.icon_path || "asset/monster/Unknown.webp";

    // 1. DEF Scaling capped at level 80 strictly
    const baseDef70 = monster.stats_lv70.def;
    const curveValL = DEFENCE_CURVE[targetMonsterLevel - 1] || 1588;
    const curveVal70 = DEFENCE_CURVE[69]; // Index 69 is level 70
    
    // Scale DEF
    const monsterDef = baseDef70 * (curveValL / curveVal70);

    // 新版队伍引擎保留减防/无视防御的原始作用域；目标面板按当前角色、
    // 当前技能页的伤害事件预览，不能再固定使用强击标签。
    const defShred = useWebTeamState
        ? sumWebScopedEffects(webBuffs.defenseEffects, previewDamageKind, "shred", previewSkillCategory, previewElement)
        : (charStats.def_shred || 0);
    let ignoreDef = useWebTeamState
        ? sumWebScopedEffects(webBuffs.defenseEffects, previewDamageKind, "ignore", previewSkillCategory, previewElement)
        : (charStats.ignore_def || 0);
    
    // Dynamically incorporate tagged ignore def bonuses matching the active skill category
    if (charStats.tagged_ignore_def_bonuses) {
        charStats.tagged_ignore_def_bonuses.forEach(b => {
            const matchCat = b.tags.includes(activeSkillCategory);
            const matchElem = b.tags.includes(charStats.element);
            if (matchCat || matchElem) {
                ignoreDef += b.value;
            }
        });
    }

    const penRate = (charStats.pen_rate || 0) / 100;
    const penFlat = charStats.pen_flat || 0;

    // Calculate effective DEF
    const defEffective = Math.max(0, monsterDef * (1 - (defShred + ignoreDef) / 100) * (1 - penRate) - penFlat);
    document.getElementById("val-boss-def").textContent = `${Math.round(monsterDef)} ➜ ${Math.round(defEffective)}`;

    // 2. Resistance displays
    const activeElem = charStats.element;
    const dmgRes = monster.resistances.damage_res;
    
    const resistMapping = {
        "physical": "val-res-physical",
        "fire": "val-res-fire",
        "ice": "val-res-ice",
        "electric": "val-res-electric",
        "wind": "val-res-wind",
        "ether": "val-res-ether"
    };

    Object.keys(resistMapping).forEach(resKey => {
        const spanId = resistMapping[resKey];
        const valSpan = document.getElementById(spanId);
        
        const baseVal = dmgRes[resKey] || 0;
        const isMatchedElem = 
            (activeElem === "物理" && resKey === "physical") ||
            (activeElem === "火属性" && resKey === "fire") ||
            (activeElem === "冰属性" && resKey === "ice") ||
            (activeElem === "电属性" && resKey === "electric") ||
            (activeElem === "风属性" && resKey === "wind") ||
            (activeElem === "以太" && resKey === "ether");
        
        const shredSources = useWebTeamState
            ? getWebScopedEffectSources(
                webBuffs.resistanceEffects,
                previewDamageKind,
                "shred",
                previewSkillCategory,
                resKey,
            )
            : [];
        const ignoreSources = useWebTeamState
            ? getWebScopedEffectSources(
                webBuffs.resistanceEffects,
                previewDamageKind,
                "ignore",
                previewSkillCategory,
                resKey,
            )
            : [];
        const shred = useWebTeamState
            ? shredSources.reduce((sum, source) => sum + source.value, 0)
            : (charStats.res_shred || 0);
        const ignore = useWebTeamState
            ? ignoreSources.reduce((sum, source) => sum + source.value, 0)
            : (charStats.res_ignore || 0);
        const afterShred = Math.max(-100, baseVal - shred);
        const effectiveVal = Math.max(-100, afterShred - ignore);
        
        valSpan.style.color = "";
        
        if (ignore > 0) {
            const rows = [...shredSources.map((source) => ({ ...source, kind: "减抗" })),
                ...ignoreSources.map((source) => ({ ...source, kind: "无视" }))]
                .map((source) => `<span class="live-stat-tooltip-row"><strong>${source.kind} ${source.value}%</strong><span>${source.label}</span></span>`)
                .join("");
            valSpan.innerHTML = `${baseVal}% ➜ <span style="color: var(--clr-green); font-weight: 600;">${afterShred.toFixed(1)}%</span> ➜ <span class="live-stat-breakdown" tabindex="0" style="color: var(--clr-cyan); font-weight: 700;">${effectiveVal.toFixed(1)}%<span class="live-stat-tooltip" role="tooltip"><span class="live-stat-tooltip-title">当前攻击的抗性修正</span>${rows}</span></span>`;
        } else if (shred > 0) {
            const rows = shredSources
                .map((source) => `<span class="live-stat-tooltip-row"><strong>减抗 ${source.value}%</strong><span>${source.label}</span></span>`)
                .join("");
            valSpan.innerHTML = `${baseVal}% ➜ <span class="live-stat-breakdown" tabindex="0" style="color: var(--clr-green); font-weight: 600;">${afterShred.toFixed(1)}%<span class="live-stat-tooltip" role="tooltip"><span class="live-stat-tooltip-title">当前攻击的抗性修正</span>${rows}</span></span>`;
        } else {
            valSpan.textContent = `${baseVal}%`;
        }
        
        if (isMatchedElem) {
            valSpan.style.color = "var(--clr-cyan)";
        }
    });

    // 3. Stun Vulnerability Config Panel - Dynamic checklist and sum calculation
    const stunContainer = document.getElementById("stun-vuln-sources-container");
    const bossStunBaseInput = document.getElementById("input-boss-stun-base");
    const bossStunBase = bossStunBaseInput ? parseFloat(bossStunBaseInput.value) : (monster.stun_extra_damage_taken_pct || 50);

    let charStunApplied = 0;
    if (stunContainer) {
        const stunList = getSquadStunVulnerability();
        if (stunList.length === 0) {
            stunContainer.innerHTML = `<span class="text-xs text-slate-500 py-1">当前队伍角色未提供额外的失衡易伤</span>`;
        } else {
            stunContainer.innerHTML = "";
            stunList.forEach(item => {
                const stateKey = `stun-vuln-${item.charId}`;
                if (activeBuffsState[stateKey] === undefined) {
                    activeBuffsState[stateKey] = true;
                }
                if (activeBuffsState[stateKey]) {
                    charStunApplied += item.value;
                }
                const isChecked = activeBuffsState[stateKey] ? "checked" : "";
                const div = document.createElement("div");
                div.className = "flex items-center gap-2 text-xs py-0.5";
                div.style.display = "flex";
                div.style.alignItems = "center";
                div.style.gap = "8px";
                div.innerHTML = `
                    <input type="checkbox" id="chk-stun-vuln-${item.charId}" ${isChecked}>
                    <label for="chk-stun-vuln-${item.charId}" class="text-slate-300 cursor-pointer">${item.name} (${item.note || '击破辅助'}): +${item.value}%</label>
                `;
                div.querySelector("input").addEventListener("change", (e) => {
                    activeBuffsState[stateKey] = e.target.checked;
                    updateUI();
                });
                stunContainer.appendChild(div);
            });
        }
    }

    document.getElementById("val-boss-stun-mult").textContent = `+${bossStunBase + charStunApplied}%`;

    // 4. Dynamic Crisis Buffs checklist loading based on Boss name
    loadCrisisBuffsForMonster(monster.name);
    
    // 5. Render Field Environment Effect
    renderFieldEnvironment(monster);
}

function loadCrisisBuffsForMonster(monsterName) {
    const container = document.getElementById("stage-buffs-container");
    if (!container) return;

    let allBuffs = getAllCrisisBuffs();

    // Filter stage crisis buffs by search keywords
    const searchInput = document.getElementById("input-search-crisis-buffs");
    const keyword = searchInput ? searchInput.value.trim().toLowerCase() : "";
    if (keyword) {
        allBuffs = allBuffs.filter(buff => 
            (buff.title && buff.title.toLowerCase().includes(keyword)) || 
            (buff.desc && buff.desc.toLowerCase().includes(keyword))
        );
    }

    if (allBuffs.length === 0) {
        container.innerHTML = `<div class="text-sm text-slate-400 p-2">未找到符合搜索条件的环境增益。</div>`;
        return;
    }

    container.innerHTML = "";
    allBuffs.forEach(buff => {
        const item = document.createElement("div");
        item.className = "flex items-start gap-2 text-sm";
        item.style.background = "rgba(255, 255, 255, 0.02)";
        item.style.padding = "0.5rem";
        item.style.borderRadius = "6px";
        item.style.border = "1px solid rgba(255, 255, 255, 0.04)";
        item.style.marginBottom = "0.25rem";

        const isChecked = selectedCrisisBuffs.has(buff.id) ? "checked" : "";

        item.innerHTML = `
            <input type="checkbox" id="chk-buff-${buff.id}" data-buff-id="${buff.id}" ${isChecked} class="form-select rounded-rect mt-1" style="width: 16px; height: 16px; min-width: 16px; cursor: pointer;">
            <div class="flex-col gap-1">
                <label for="chk-buff-${buff.id}" class="font-semibold text-xs text-glow cursor-pointer">${buff.title}</label>
                <p class="text-xs text-slate-300">${formatHtmlColors(buff.desc)}</p>
            </div>
        `;

        item.querySelector("input").addEventListener("change", (e) => {
            if (e.target.checked) {
                selectedCrisisBuffs.add(buff.id);
            } else {
                selectedCrisisBuffs.delete(buff.id);
            }
            updateUI();
        });

        container.appendChild(item);
    });
}

// =====================================================================
// 10. MULTIPLIER HELPERS AND COMBAT SETTLEMENT CALCULATOR ENGINE
// =====================================================================
function getTaggedDazeBonus(charStats, skillCategory) {
    let bonus = 0;
    if (charStats.tagged_daze_bonuses) {
        charStats.tagged_daze_bonuses.forEach(b => {
            if (b.tags && b.tags.includes(skillCategory)) bonus += b.value;
        });
    }
    return bonus;
}

function getTaggedDmgBonus(charStats, skillCategory, element) {
    let bonus = 0;
    if (charStats.tagged_dmg_bonuses) {
        charStats.tagged_dmg_bonuses.forEach(b => {
            const matchesCategory = b.tags.includes(skillCategory);
            const matchesElement = b.tags.includes(element) || 
                                   (element === "火属性" && b.tags.includes("fire")) ||
                                   (element === "冰属性" && b.tags.includes("ice")) ||
                                   (element === "电属性" && b.tags.includes("electric")) ||
                                   (element === "风属性" && b.tags.includes("wind")) ||
                                   (element === "以太" && b.tags.includes("ether")) ||
                                   (element === "物理" && b.tags.includes("physical"));
            if (matchesCategory || matchesElement) bonus += b.value;
        });
    }
    return bonus;
}

function getAdditionalMultiplier(charStats, skillCategory, skillName) {
    let add = 0;
    if (charStats.additional_multipliers) {
        charStats.additional_multipliers.forEach(m => {
            const matchesCategory = m.tags.includes(skillCategory);
            const matchesName = skillName && m.tags.some(t => skillName.includes(t));
            if (matchesCategory || matchesName) add += m.value;
        });
    }
    return add;
}

function getMultiplierRatio(charStats, skillCategory, skillName) {
    let ratio = 1.0;
    if (charStats.multiplier_ratios) {
        charStats.multiplier_ratios.forEach(r => {
            const matchesCategory = r.tags.includes(skillCategory);
            const matchesName = skillName && r.tags.some(t => skillName.includes(t));
            if (matchesCategory || matchesName) ratio *= (1 + r.value / 100);
        });
    }
    return ratio;
}

const LEVEL_COEFFICIENTS = {
    1: 50, 2: 54, 3: 58, 4: 62, 5: 66, 6: 71, 7: 76, 8: 82, 9: 88, 10: 94,
    11: 100, 12: 107, 13: 114, 14: 121, 15: 129, 16: 137, 17: 145, 18: 153, 19: 162, 20: 172,
    21: 181, 22: 191, 23: 201, 24: 211, 25: 222, 26: 233, 27: 245, 28: 256, 29: 268, 30: 281,
    31: 293, 32: 306, 33: 319, 34: 333, 35: 347, 36: 361, 37: 375, 38: 390, 39: 405, 40: 421,
    41: 436, 42: 452, 43: 469, 44: 485, 45: 502, 46: 519, 47: 537, 48: 555, 49: 573, 50: 592,
    51: 610, 52: 629, 53: 649, 54: 669, 55: 689, 56: 709, 57: 730, 58: 751, 59: 772
};

function getLevelCoefficient(level) {
    if (level >= 60) return 794;
    return LEVEL_COEFFICIENTS[level] || 794;
}

function webScopeMatches(scope, damageKind, skillCategory = null, element = null) {
    if (!scope) return true;
    if (Array.isArray(scope.damageKinds) && !scope.damageKinds.includes(damageKind)) return false;
    if (Array.isArray(scope.skillCategories) && (!skillCategory || !scope.skillCategories.includes(skillCategory))) return false;
    if (Array.isArray(scope.elements) && (!element || !scope.elements.includes(element))) return false;
    return true;
}

function sumWebScopedEffects(effects, damageKind, effectKind = null, skillCategory = null, element = null) {
    if (!Array.isArray(effects)) return 0;
    return effects.reduce((sum, effect) => {
        if (effectKind && effect && effect.kind !== effectKind) return sum;
        if (!webScopeMatches(effect && effect.scope, damageKind, skillCategory, element)) return sum;
        return sum + (Number(effect && effect.percent) || 0);
    }, 0);
}

function getWebScopedEffectSources(effects, damageKind, effectKind, skillCategory = null, element = null) {
    if (!Array.isArray(effects)) return [];
    return effects
        .filter((effect) => (!effectKind || effect?.kind === effectKind) &&
            webScopeMatches(effect?.scope, damageKind, skillCategory, element))
        .map((effect) => ({
            id: effect.sourceId || `${effectKind}:${effect.label || effect.percent}`,
            label: effect.label || (effectKind === "ignore" ? "抗性无视" : "抗性降低"),
            value: Number(effect.percent) || 0,
        }));
}

function sumWebScopedDamageBonuses(effects, damageKind, skillCategory, element) {
    if (!Array.isArray(effects)) return 0;
    return effects.reduce((sum, effect) => {
        if (!webScopeMatches(effect && effect.scope, damageKind, skillCategory, element)) return sum;
        return sum + (Number(effect && effect.percent) || 0);
    }, 0);
}

function resolveDamageSkillCategory(category, skillName) {
    if (category === "chain" && skillName && skillName.includes("终结技")) return "ultimate";
    return category;
}

function getWebElementDamageBonus(panel, elementKey) {
    if (!panel) return 0;
    const values = {
        physical: panel.physicalDmgBonus,
        fire: panel.fireDmgBonus,
        ice: panel.iceDmgBonus,
        electric: panel.electricDmgBonus,
        ether: panel.etherDmgBonus,
        wind: panel.windDmgBonus,
    };
    return Number(values[elementKey]) || 0;
}

function renderCombatSettlementEngine(activeChar, charStats, webTeamState = null) {
    const dash = document.getElementById("settlement-dashboard");
    if (!dash) return;

    const charData = DB.characters[activeChar.characterId];
    const monster = DB.monsters[targetMonsterId];
    const webBuffs = webTeamState && webTeamState.buffs;
    const webPanel = webTeamState && webTeamState.activePanel;
    const useWebTeamState = Boolean(webBuffs && webPanel);

    if (!charData || !monster) return;

    const activeSkillsGroup = charData.skills[activeSkillCategory];
    if (!activeSkillsGroup || activeSkillsGroup.length === 0) {
        dash.innerHTML = `<div class="text-slate-400 text-center py-6">当前角色在此技能分类下无可用招式数据。</div>`;
        return;
    }

    dash.innerHTML = "";

    // 1. Calculate defense multipliers
    const charLevelInput = document.getElementById("select-char-level");
    const charLevel = charLevelInput ? parseInt(charLevelInput.value) || 60 : 60;
    const defConstant = getLevelCoefficient(charLevel);
    
    // Scale Monster DEF based on Level capped at 80
    const baseDef70 = monster.stats_lv70.def;
    const curveValL = DEFENCE_CURVE[targetMonsterLevel - 1] || 1588;
    const curveVal70 = DEFENCE_CURVE[69];
    const monsterDef = baseDef70 * (curveValL / curveVal70);

    const penRatio = charStats.pen_rate / 100;
    const penFlat = charStats.pen_flat;
    const defShred = useWebTeamState
        ? sumWebScopedEffects(webBuffs.defenseEffects, "assault", "shred")
        : (charStats.def_shred || 0);
    const ignoreDef = useWebTeamState
        ? sumWebScopedEffects(webBuffs.defenseEffects, "assault", "ignore")
        : (charStats.ignore_def || 0);

    const defEffective = Math.max(0, monsterDef * (1 - (defShred + ignoreDef) / 100) * (1 - penRatio) - penFlat);
    const defMultiplier = defConstant / (defEffective + defConstant);

    // 2. Element Resistance Multiplier calculation
    let dbKey = "physical";
    if (charStats.element === "火属性") dbKey = "fire";
    else if (charStats.element === "冰属性") dbKey = "ice";
    else if (charStats.element === "电属性") dbKey = "electric";
    else if (charStats.element === "风属性") dbKey = "wind";
    else if (charStats.element === "以太") dbKey = "ether";

    const baseMonsterResist = monster.resistances.damage_res[dbKey] || 0; // percentage
    const resistShredPercent = useWebTeamState
        ? sumWebScopedEffects(webBuffs.resistanceEffects, "assault", "shred")
        : (charStats.res_shred || 0);
    const resistIgnorePercent = useWebTeamState
        ? sumWebScopedEffects(webBuffs.resistanceEffects, "assault", "ignore")
        : (charStats.res_ignore || 0);
    let resistReduction = (resistShredPercent + resistIgnorePercent) / 100; // Extra resist reductions if any

    const resistMultiplier = 1 - (baseMonsterResist / 100 - resistReduction);

    // 3. Stun Damage Taken Multiplier calculation
    // 3. Stun Damage Taken Multiplier calculation
    let stunMultiplier = 1.0;
    const bossStunBaseInput = document.getElementById("input-boss-stun-base");
    const bossStunBase = bossStunBaseInput ? parseFloat(bossStunBaseInput.value) : (monster.stun_extra_damage_taken_pct || 50);
    
    let charStunApplied = 0;
    let hasBanjiConstantVuln = false; // 新增：用于精准追踪扳机的易伤是否被勾选生效

    const stunList = getSquadStunVulnerability();
    stunList.forEach(item => {
        const stateKey = `stun-vuln-${item.charId}`;
        if (activeBuffsState[stateKey] === undefined) {
            activeBuffsState[stateKey] = true;
        }
        if (activeBuffsState[stateKey]) {
            charStunApplied += item.value;
            // 如果生效的易伤来源包含扳机，则打上常态覆盖标记
            if (item.charId === "1361") {
                hasBanjiConstantVuln = true;
            }
        }
    });

    const stunCapture = useWebTeamState && Array.isArray(webBuffs.stunVulnerabilityCaptures)
        ? webBuffs.stunVulnerabilityCaptures.reduce((best, item) =>
            !best || item.maxBonusPercent > best.maxBonusPercent ? item : best, null)
        : null;

    if (stunCapture) {
        // 帷幕易伤先快照“怪物自带失衡易伤 + 角色施加的失衡易伤”，再按
        // 规则数据给出的上限截断。该规则 target=self，因此只会出现在
        // 叶瞬光作为当前攻击者的 webBuffs 中，不会拐到队友。
        const capturedVulnerability = Math.min(
            Number(stunCapture.maxBonusPercent) || 0,
            bossStunBase + charStunApplied,
        );
        stunMultiplier = (100 + capturedVulnerability) / 100;
    } else if (stunnedState) {
        // 失衡期：基础 100% + 怪物自带易伤 + 角色施加的易伤 (此时包含扳机的 35% 或 55%)
        stunMultiplier = (100 + bossStunBase + charStunApplied) / 100;
    } else {
        // 非失衡期（常态）
        if (hasBanjiConstantVuln) {
            // 常态下剔除怪物自带易伤，只吃角色施加的额外易伤
            stunMultiplier = (100 + charStunApplied) / 100;
        } else {
            stunMultiplier = 1.0; 
        }
    }

    // 4. Crisis Buffs Multipliers sums
    const crisisEffects = getSelectedCrisisBuffEffects();
    const crisisDmgMultiplierSum = crisisEffects.reduce((sum, effect) => sum + effect.damageBonus, 0);
    const crisisAtkPctSum = crisisEffects.reduce((sum, effect) => sum + effect.attackPercent, 0);

    // 5. Total damage bonus calculation
    const baseAtk = (useWebTeamState ? webPanel.atk : charStats.atk) * (1 + crisisAtkPctSum / 100);
    const weaponPassiveDmg = charStats.weapon_dmg_bonus || 0;

    // 5b. Cinema skill level boost calculation
    let resolvedSkillLevel = activeSkillLevel; // e.g. "lv12"
    let skillLevelText = activeSkillLevel.toUpperCase(); // e.g. "LV12"

    const baseLevelNum = parseInt(activeSkillLevel.replace("lv", "")) || 12;
    let boost = 0;
    
    if (activeChar.cinema >= 3 && (activeSkillCategory === "basic" || activeSkillCategory === "dodge" || activeSkillCategory === "assist")) {
        boost = 2;
    } else if (activeChar.cinema >= 5 && (activeSkillCategory === "special" || activeSkillCategory === "chain")) {
        boost = 2;
    }

    if (boost > 0) {
        const finalLevelNum = Math.min(16, baseLevelNum + boost);
        resolvedSkillLevel = "lv" + finalLevelNum;
        skillLevelText = `${activeSkillLevel.toUpperCase()} (+${boost} 影画提升 ➜ ${resolvedSkillLevel.toUpperCase()})`;
    }
    
    // Build responsive expected hits list and potential side-by-side anomaly panel
    let skillsContainer = dash;
    let anomalyContainer = null;

    if (charData.specialty === "异常") {
        dash.style.display = "grid";
        dash.style.gridTemplateColumns = "1.2fr 0.8fr";
        dash.style.gap = "1rem";
        dash.style.maxHeight = "350px";

        // Create skills column container
        const leftCol = document.createElement("div");
        leftCol.className = "flex-col gap-3 scroll-container";
        leftCol.style.overflowY = "auto";
        leftCol.style.maxHeight = "230px";
        leftCol.style.paddingRight = "0.25rem";
        
        // Create anomaly column container
        const rightCol = document.createElement("div");
        rightCol.className = "flex-col gap-3 scroll-container";
        rightCol.style.overflowY = "auto";
        rightCol.style.maxHeight = "230px";
        rightCol.style.paddingRight = "0.25rem";

        dash.appendChild(leftCol);
        dash.appendChild(rightCol);

        skillsContainer = leftCol;
        anomalyContainer = rightCol;
    } else {
        dash.style.display = "flex";
        dash.style.flexDirection = "column";
        dash.style.gap = "0.6rem";
        dash.style.maxHeight = "240px";
    }

    activeSkillsGroup.forEach(skill => {
        const skillCard = document.createElement("div");
        skillCard.className = "stats-overview-box flex-col gap-2";
        skillCard.style.background = "rgba(10, 5, 25, 0.4)";
        skillCard.style.borderLeft = "4px solid var(--clr-cyan)";

        skillCard.innerHTML = `
            <div class="flex justify-between items-center border-b pb-1">
                <strong class="text-sm text-glow font-semibold">${skill.sub_skill_name}</strong>
                <span class="text-xs text-slate-400">${activeSkillCategory.toUpperCase()} / 技能等级: ${skillLevelText}</span>
            </div>
            <p class="text-xs text-slate-400 mb-2">${formatHtmlColors(skill.sub_skill_desc)}</p>
            <div class="expected-hits-grid flex-col gap-2">
                <!-- Hits dynamic formulas render -->
            </div>
        `;

        const hitsGrid = skillCard.querySelector(".expected-hits-grid");
        
        let hasHits = false;
        skill.parameters.forEach(p => {
            const rawVal = p.values[resolvedSkillLevel] !== undefined ? p.values[resolvedSkillLevel] : p.values[activeSkillLevel];
            if (rawVal === undefined || rawVal === null) return;
            
            hasHits = true;
            
            const isDaze = p.param_name.includes("失衡") || p.param_name.includes("daze");
            const row = document.createElement("div");
            row.style.background = "rgba(0,0,0,0.25)";
            row.style.borderRadius = "6px";
            row.style.padding = "0.4rem 0.6rem";
            row.className = "flex justify-between items-center text-xs";

            if (isDaze) {
                // Bifurcated Stun/Daze calculation pathway
                const taggedDaze = getTaggedDazeBonus(charStats, activeSkillCategory);
                const totalDazePercent = (charStats.daze_bonus || 0) + taggedDaze;
                const dazeVal = charStats.impact * (rawVal / 100) * (1 + totalDazePercent / 100);

                row.innerHTML = `
                    <div class="flex-col">
                        <span class="font-semibold text-glow" style="color: var(--clr-lime, #2BAD00); text-shadow: 0 0 8px rgba(43,173,0,0.4);">${p.param_name}</span>
                        <span class="text-xs text-slate-400">失衡倍率: ${rawVal}%</span>
                    </div>
                    <div class="flex gap-4 items-center">
                        <div class="text-right">
                            <span class="text-slate-400 block" style="font-size: 0.6rem;">失衡贡献值 (基于冲击力结算)</span>
                            <strong style="color: var(--clr-lime, #2BAD00); font-family: var(--font-display); font-size: 1.1rem; text-shadow: 0 0 10px rgba(43,173,0,0.5);">${Math.round(dazeVal)}</strong>
                        </div>
                    </div>
                `;
            } else {
                // Regular damage pathway with tagged buffs and special multipliers
                const addMult = getAdditionalMultiplier(charStats, activeSkillCategory, skill.sub_skill_name);
                const multRatio = getMultiplierRatio(charStats, activeSkillCategory, skill.sub_skill_name);
                const damageSkillCategory = resolveDamageSkillCategory(activeSkillCategory, skill.sub_skill_name);
                const taggedDmgBonus = getTaggedDmgBonus(charStats, damageSkillCategory, charStats.element);
                const scopedWebDamageBonus = useWebTeamState
                    ? sumWebScopedDamageBonuses(
                        webBuffs.scopedDamageBonusEffects,
                        "direct",
                        damageSkillCategory,
                        dbKey,
                    )
                    : 0;
                const regularDmgBonus = useWebTeamState
                    ? (
                        getWebElementDamageBonus(webPanel, dbKey) +
                        webBuffs.normalDamageBonusPercent +
                        scopedWebDamageBonus +
                        crisisDmgMultiplierSum
                    ) / 100
                    : (charStats.attribute_dmg / 100) + (weaponPassiveDmg / 100) +
                      (crisisDmgMultiplierSum / 100) + (taggedDmgBonus / 100);

                let damageMultiplier = 1 + regularDmgBonus;
                if (charData.specialty === "命破") {
                    damageMultiplier = (1 + regularDmgBonus) * (1 + (charStats.pen_dmg_bonus || 0) / 100);
                }

                const skillMult = (rawVal + addMult) / 100 * multRatio;

                const skillDefShred = useWebTeamState
                    ? sumWebScopedEffects(webBuffs.defenseEffects, "direct", "shred", damageSkillCategory, dbKey)
                    : defShred;
                let skillIgnoreDef = useWebTeamState
                    ? sumWebScopedEffects(webBuffs.defenseEffects, "direct", "ignore", damageSkillCategory, dbKey)
                    : ignoreDef;
                if (!useWebTeamState && charStats.tagged_ignore_def_bonuses) {
                    charStats.tagged_ignore_def_bonuses.forEach(b => {
                        const matchCat = b.tags.includes(damageSkillCategory);
                        const matchElem = b.tags.includes(charStats.element);
                        if (matchCat || matchElem) {
                            skillIgnoreDef += b.value;
                        }
                    });
                }

                const skillDefEffective = Math.max(0, monsterDef * (1 - (skillDefShred + skillIgnoreDef) / 100) * (1 - penRatio) - penFlat);
                let activeDefMult = defConstant / (skillDefEffective + defConstant);
                const skillResistShred = useWebTeamState
                    ? sumWebScopedEffects(webBuffs.resistanceEffects, "direct", "shred", damageSkillCategory, dbKey)
                    : resistShredPercent;
                const skillResistIgnore = useWebTeamState
                    ? sumWebScopedEffects(webBuffs.resistanceEffects, "direct", "ignore", damageSkillCategory, dbKey)
                    : resistIgnorePercent;
                const activeResistMultiplier = 1 - (
                    baseMonsterResist / 100 - (skillResistShred + skillResistIgnore) / 100
                );
                
                let baseDamage = baseAtk * skillMult;
                if (charData.specialty === "命破") {
                    baseDamage = charStats.breach_power * skillMult;
                    activeDefMult = 1.0;
                }

                const nonCritDmg = baseDamage * damageMultiplier * activeResistMultiplier * activeDefMult * stunMultiplier;
                const scopedCritDamageBonus = useWebTeamState
                    ? sumWebScopedEffects(
                        webBuffs.critDamageBonusEffects,
                        "direct",
                        null,
                        damageSkillCategory,
                        dbKey,
                    )
                    : 0;
                const critDmg = nonCritDmg * (1 + (charStats.crit_dmg + scopedCritDamageBonus) / 100);
                
                const critRateClamped = Math.min(1.0, Math.max(0, charStats.crit_rate / 100));
                const averageDmg = nonCritDmg * (1 - critRateClamped) + critDmg * critRateClamped;

                row.innerHTML = `
                    <div class="flex-col">
                        <span class="font-semibold text-glow">${p.param_name}</span>
                        <span class="text-xs text-slate-400">倍率: ${rawVal}%${addMult > 0 ? ` + 额外倍率: ${addMult}%` : ""}${multRatio !== 1.0 ? ` × 倍率系数: ${multRatio.toFixed(2)}` : ""}</span>
                    </div>
                    <div class="flex gap-4">
                        <div class="text-center"><span class="text-slate-400 block" style="font-size: 0.6rem;">普通未暴击</span><strong style="color: var(--text-primary); font-family: var(--font-display);">${Math.round(nonCritDmg)}</strong></div>
                        <div class="text-center"><span class="text-slate-400 block" style="font-size: 0.6rem;">暴击伤害</span><strong style="color: var(--clr-gold); font-family: var(--font-display);">${Math.round(critDmg)}</strong></div>
                        <div class="text-center"><span class="text-slate-400 block" style="font-size: 0.6rem;">期望平均伤害</span><strong class="highlight-text" style="font-family: var(--font-display);">${Math.round(averageDmg)}</strong></div>
                    </div>
                `;
            }

            hitsGrid.appendChild(row);
        });

        if (!hasHits) {
            hitsGrid.innerHTML = `<div class="text-xs text-slate-400 text-center py-2">暂无当前技能等级的具体伤害倍率数据。</div>`;
        }

        skillsContainer.appendChild(skillCard);
    });

    // ===================================================================
    // ANOMALY DAMAGE SETTLEMENT PANEL (for 异常 specialty characters only)
    // ===================================================================
    if (charData.specialty === "异常") {
        const ANOMALY_TABLE = {
            "物理":   { name: "强击", baseRatio: 713, sustained: false, duration: 10, tickInterval: null, remainPerSec: 7.5 },
            "冰属性": { name: "碎冰", baseRatio: 500, sustained: false, duration: 10, tickInterval: null, remainPerSec: 7.5 },
            "火属性": { name: "灼烧", baseRatio: 50,  sustained: true,  duration: 10, tickInterval: 0.5, remainPerSec: null, remainFormula: (rem) => (rem / 0.5) * 50 },
            "电属性": { name: "感电", baseRatio: 125, sustained: true,  duration: 10, tickInterval: 1.0, remainPerSec: null, remainFormula: (rem) => rem * 125 },
            "以太":   { name: "侵蚀", baseRatio: 62.5, sustained: true, duration: 10, tickInterval: 0.5, remainPerSec: null, remainFormula: (rem) => (rem / 0.5) * 62.5 },
        };

        const elem = charStats.element;
        const anomalyInfo = ANOMALY_TABLE[elem];

        if (anomalyInfo) {
            const levelFactor = 1 + (charLevel - 1) / 59;
            const apFactor = (charStats.anomaly_proficiency || 0) / 100;

            // 新版队伍桥接直接消费统一解析结果，避免旧版 activeBuffsState
            // 漏掉队友音擎以及“先加音擎掌控、再求角色额外能力”的依赖。
            let regularAnomalyBonus;
            if (useWebTeamState) {
                regularAnomalyBonus = (
                    getWebElementDamageBonus(webPanel, dbKey) +
                    webBuffs.normalDamageBonusPercent
                ) / 100 + crisisDmgMultiplierSum / 100;
            } else {
                // Legacy fallback: attribute_dmg + weapon + crisis + element tags.
                regularAnomalyBonus = (charStats.attribute_dmg / 100) + (weaponPassiveDmg / 100) + (crisisDmgMultiplierSum / 100);
                if (charStats.tagged_dmg_bonuses) {
                    charStats.tagged_dmg_bonuses.forEach(b => {
                        if (b.tags.includes("anomaly")) return; // skip, these go to anomaly zone
                        const matchesElement = b.tags.includes(elem) ||
                            (elem === "物理" && b.tags.includes("physical")) ||
                            (elem === "火属性" && b.tags.includes("fire")) ||
                            (elem === "冰属性" && b.tags.includes("ice")) ||
                            (elem === "电属性" && b.tags.includes("electric")) ||
                            (elem === "以太" && b.tags.includes("ether"));
                        if (matchesElement) regularAnomalyBonus += b.value / 100;
                    });
                }
            }
            const regularDmgMult = 1 + regularAnomalyBonus;

            // Anomaly DMG zone (independent multiplier)
            // Anomaly DMG zone (independent multipliers)
            const anomalyBonusPercent = useWebTeamState
                ? webBuffs.anomalyDamageBonusPercent
                : (charStats.pure_anomaly_dmg_bonus || 0);
            const disorderBonusPercent = useWebTeamState
                ? webBuffs.disorderDamageBonusFromSourcePercent + webBuffs.disorderDamageBonusFromTriggererPercent
                : (charStats.disorder_dmg_bonus || 0);
            const pureAnomalyDmgMult = 1 + anomalyBonusPercent / 100;
            const disorderDmgMult = 1 + disorderBonusPercent / 100;
            const corePassiveBonus = useWebTeamState
                ? webBuffs.fixedDisorderMultiplierPercent
                : (charStats.disorder_ratio_bonus || 0);

            // 新版引擎桥接：保留旧版公式作为回退，但实际网页结算优先消费
            // dist/src/domain/engine 下的 TypeScript 新引擎。这里不改动原有 DOM。
            const newEngine = globalThis.ZZZ_NEW_ENGINE;
            const legacyVulnerabilityPercent = Math.max(0, stunMultiplier * 100 - 100);
            const resolvedVulnerabilityPercent = useWebTeamState
                ? sumWebScopedEffects(webBuffs.vulnerabilityEffects, "assault", null, null, dbKey)
                : 0;
            // 迁移期间旧页面仍负责怪物自带失衡易伤，以及尚未迁移的角色来源；
            // 已由统一规则解析的易伤会作为 vulnerabilityEffects 进入新引擎，
            // 因此这里只传递旧值中尚未被规则覆盖的部分，避免重复结算。
            const vulnerabilityPercent = useWebTeamState
                ? Math.max(0, legacyVulnerabilityPercent - resolvedVulnerabilityPercent)
                : legacyVulnerabilityPercent;
            const newEngineInputBase = {
                characterLevel: charLevel,
                attackPower: baseAtk,
                anomalyProficiency: useWebTeamState ? webPanel.anomalyProficiency : (charStats.anomaly_proficiency || 0),
                normalDamageBonusPercent: regularAnomalyBonus * 100,
                anomalyEffectStrengthMultiplierPercent: 0,
                damageKind: "assault",
                anomalySkillMultiplierPercent: anomalyInfo.baseRatio,
                anomalyDamageBonusPercent: anomalyBonusPercent,
                anomalyCritMultiplier: charStats.anomaly_crit_multiplier || 1,
                critProfiles: useWebTeamState ? webBuffs.critProfiles : undefined,
                critDamageBonusEffects: useWebTeamState ? webBuffs.critDamageBonusEffects : undefined,
                sourceMemberId: String(activeChar.characterId),
                triggererMemberId: String(activeChar.characterId),
                anomalySourceMemberId: String(activeChar.characterId),
                skillCategory: activeSkillCategory === "chain" ? "ultimate" : activeSkillCategory,
                derivedDamageEffects: useWebTeamState ? webBuffs.derivedDamageEffects : undefined,
                extraDamageMultiplierPercent: 100,
                extraDamageBonusPercent: useWebTeamState ? webBuffs.yifangDamageBonusPercent : 0,
                disorderSource: dbKey === "physical" ? "physical" :
                    dbKey === "ice" ? "frost" :
                    dbKey === "fire" ? "burn" :
                    dbKey === "electric" ? "electric" :
                    dbKey === "ether" ? "corrosion" : "wind",
                disorderVariant: "normal",
                remainingSeconds: anomalyInfo.duration,
                fixedDisorderMultiplierPercent: corePassiveBonus,
                disorderDamageBonusFromSourcePercent: useWebTeamState
                    ? webBuffs.disorderDamageBonusFromSourcePercent
                    : (charStats.disorder_dmg_bonus || 0),
                disorderDamageBonusFromTriggererPercent: useWebTeamState
                    ? webBuffs.disorderDamageBonusFromTriggererPercent
                    : 0,
                polarDisorderPercent: 0,
                polarAnomalyMasterySkillMultiplierPercent: 0,
                currentAnomalyMastery: useWebTeamState ? webPanel.anomalyMastery : (charStats.anomaly_mastery || 0),
                triggererAttackPower: baseAtk,
                turbulenceSource: dbKey === "physical" ? "physical" :
                    dbKey === "ice" ? "frost" :
                    dbKey === "fire" ? "burn" :
                    dbKey === "electric" ? "electric" : "corrosion",
                windAnomalyPresent: false,
                additionalTurbulenceMultiplierPercent: 0,
                turbulenceDamageBonusPercent: 0,
                turbulenceCritMultiplier: 1,
                monster: {
                    attackerLevel: charLevel,
                    monsterLevel: targetMonsterLevel,
                    monsterDefenseAtLevel70: baseDef70,
                    baseResistancePercent: baseMonsterResist,
                    // 新版引擎接收带作用域的效果原件；不要先把 def-shred 和
                    // def-ignore 压成一个预计算数字，否则会把“仅强击无视防御”
                    // 错当成全局减防。
                    defenseShredPercent: useWebTeamState ? 0 : defShred,
                    defenseIgnorePercent: useWebTeamState ? 0 : ignoreDef,
                    defenseEffects: useWebTeamState ? webBuffs.defenseEffects : undefined,
                    penetrationRatePercent: charStats.pen_rate || 0,
                    penetrationFlat: penFlat,
                    resistanceShredPercent: useWebTeamState ? 0 : (charStats.res_shred || 0),
                    resistanceIgnorePercent: useWebTeamState ? 0 : (charStats.res_ignore || 0),
                    resistanceEffects: useWebTeamState ? webBuffs.resistanceEffects : undefined,
                    vulnerabilityEffects: useWebTeamState ? webBuffs.vulnerabilityEffects : undefined,
                    vulnerabilityPercent,
                    damageKind: "assault",
                    element: dbKey,
                },
            };

            // --- Anomaly Damage ---
            let anomalyLabel, anomalyDmg, newAnomalyResult;
            if (anomalyInfo.sustained) {
                // Sustained: show per-tick damage
                newAnomalyResult = newEngine?.calculateWebDamage(newEngineInputBase);
                anomalyDmg = newAnomalyResult?.trace && newAnomalyResult.trace.supported !== false
                    ? newAnomalyResult.trace.finalValue
                    : baseAtk * (anomalyInfo.baseRatio / 100) * apFactor * levelFactor * regularDmgMult * pureAnomalyDmgMult * defMultiplier * resistMultiplier * stunMultiplier;
                anomalyLabel = `${anomalyInfo.name} (每跳伤害, 每${anomalyInfo.tickInterval}s)`;
            } else {
                // One-time: show total damage
                newAnomalyResult = newEngine?.calculateWebDamage(newEngineInputBase);
                anomalyDmg = newAnomalyResult?.trace && newAnomalyResult.trace.supported !== false
                    ? newAnomalyResult.trace.finalValue
                    : baseAtk * (anomalyInfo.baseRatio / 100) * apFactor * levelFactor * regularDmgMult * pureAnomalyDmgMult * defMultiplier * resistMultiplier * stunMultiplier;
                anomalyLabel = `${anomalyInfo.name} (一次性伤害)`;
            }

            const derivedDamageHtml = (newAnomalyResult?.derivedCandidates || []).map(candidate => {
                const trace = candidate.trace;
                const finalValue = trace?.damage?.finalValue;
                if (!Number.isFinite(finalValue)) return "";
                const modeLabel = trace.mode === "replace-anomaly"
                    ? `替换异常倍率: ${trace.anomalySkillMultiplierPercent}%`
                    : `原异常倍率 × ${trace.extraDamageMultiplierPercent}%`;
                return `
                    <div style="background: rgba(0,0,0,0.45); border-radius: 6px; padding: 0.6rem; margin-top: 0.5rem;">
                        <span class="text-xs text-slate-400 block" style="margin-bottom: 0.2rem;">${trace.label || "派生异常伤害"} (${modeLabel})</span>
                        <strong style="color: var(--clr-cyan, #22d3ee); font-family: var(--font-display); font-size: 1.4rem; text-shadow: 0 0 12px rgba(34,211,238,0.55);">${Math.round(finalValue).toLocaleString()}</strong>
                    </div>
                `;
            }).join("");

            // --- Disorder Damage ---
            const disorderBase = 450;
            let remainingRatio;
            if (anomalyInfo.remainPerSec !== null) {
                remainingRatio = anomalyInfo.duration * anomalyInfo.remainPerSec;
            } else {
                remainingRatio = anomalyInfo.remainFormula(anomalyInfo.duration);
            }
            const disorderTotalRatio = disorderBase + corePassiveBonus + remainingRatio;
            const disorderInput = {
                ...newEngineInputBase,
                damageKind: "disorder",
                monster: { ...newEngineInputBase.monster, damageKind: "disorder" },
            };
            const newDisorderResult = newEngine?.calculateWebDamage(disorderInput);
            const disorderDmg = newDisorderResult?.trace && newDisorderResult.trace.supported !== false
                ? newDisorderResult.trace.finalValue
                : baseAtk * (disorderTotalRatio / 100) * apFactor * levelFactor * regularDmgMult * disorderDmgMult * defMultiplier * resistMultiplier * stunMultiplier;
            // --- Render Panel ---
            const anomalyCard = document.createElement("div");
            anomalyCard.className = "stats-overview-box flex-col gap-2";
            anomalyCard.style.background = "rgba(25, 5, 40, 0.55)";
            anomalyCard.style.border = "1px solid rgba(168, 85, 247, 0.3)";
            anomalyCard.style.borderLeft = "4px solid var(--clr-purple, #a855f7)";
            anomalyCard.style.borderRadius = "8px";
            anomalyCard.style.padding = "0.75rem";
            anomalyCard.style.boxShadow = "0 4px 20px rgba(0,0,0,0.4)";
            anomalyCard.style.marginTop = "0";

            const apDisplay = (charStats.anomaly_proficiency || 0).toFixed(0);
            const dmgZoneDisplay = (regularAnomalyBonus * 100).toFixed(1);
            const anomalyZoneDisplay = anomalyBonusPercent.toFixed(1);
            const disorderZoneDisplay = disorderBonusPercent.toFixed(1);
            const disorderRatioDisplay = disorderTotalRatio.toFixed(1);
            const normalBonusSources = useWebTeamState && Array.isArray(webBuffs.normalDamageBonusSources)
                ? webBuffs.normalDamageBonusSources
                    .map(source => `${source.label} +${Number(source.value).toFixed(1)}%`)
                    .join(" + ")
                : "旧版数据路径";

            anomalyCard.innerHTML = `
                <div class="flex justify-between items-center border-b pb-1.5" style="border-color: rgba(168,85,247,0.3);">
                    <strong class="text-sm" style="color: var(--clr-purple, #a855f7); text-shadow: 0 0 8px rgba(168,85,247,0.5);">🔮 纯净异常与紊乱结算</strong>
                </div>
                <div class="flex-col gap-2" style="margin-top: 0.5rem; font-size: 0.7rem; color: var(--text-secondary);">
                    <div class="flex justify-between"><span>异常精通 (AP):</span><strong class="highlight-text">${apDisplay}</strong></div>
                    <div class="flex justify-between"><span>常规增伤乘区:</span><strong>+${dmgZoneDisplay}%</strong></div>
                    <div class="flex justify-between"><span>异常增伤乘区:</span><strong>+${anomalyZoneDisplay}%</strong></div>
                    <div class="flex justify-between"><span>紊乱增伤乘区:</span><strong>+${disorderZoneDisplay}%</strong></div>
                    <div class="flex justify-between"><span>防御区/抗性区/失衡区:</span><strong>已实时结算应用</strong></div>
                </div>
                <div style="font-size: 0.65rem; color: var(--text-secondary); margin-top: 0.45rem; line-height: 1.5;">
                    <span style="color: var(--clr-cyan, #22d3ee);">常规增伤规则来源：</span>${normalBonusSources}
                    <br><span style="color: var(--clr-cyan, #22d3ee);">说明：</span>物理伤害加成、暴击伤害和异常独立增伤分别属于独立字段，不重复并入常规增伤来源。
                </div>
                <div style="background: rgba(0,0,0,0.45); border-radius: 6px; padding: 0.6rem; margin-top: 0.5rem;">
                    <span class="text-xs text-slate-400 block" style="margin-bottom: 0.2rem;">${anomalyLabel} (倍率: ${anomalyInfo.baseRatio}%)</span>
                    <strong style="color: var(--clr-purple, #a855f7); font-family: var(--font-display); font-size: 1.4rem; text-shadow: 0 0 12px rgba(168,85,247,0.6);">${Math.round(anomalyDmg).toLocaleString()}</strong>
                </div>
                ${derivedDamageHtml}
                <div style="background: rgba(0,0,0,0.45); border-radius: 6px; padding: 0.6rem; margin-top: 0.5rem;">
                    <span class="text-xs text-slate-400 block" style="margin-bottom: 0.2rem;">全额结算紊乱伤害 (倍率: ${disorderRatioDisplay}%)</span>
                    <strong style="color: var(--clr-gold, #F0D12B); font-family: var(--font-display); font-size: 1.4rem; text-shadow: 0 0 12px rgba(240,209,43,0.6);">${Math.round(disorderDmg).toLocaleString()}</strong>
                </div>
            `;

            if (anomalyContainer) {
                anomalyContainer.appendChild(anomalyCard);
            } else {
                dash.appendChild(anomalyCard);
            }
        }
    }
}

// =====================================================================
// 10. CONFIGURATION EXPORT & IMPORT UTILITIES
// =====================================================================
function mapMiyousheBuildsToLegacySquadConfig(imported) {
    if (!imported || !Array.isArray(imported.builds)) return null;

    const mainStatNames = {
        hp: "生命值百分比",
        hpPct: "生命值百分比",
        atk: "攻击力",
        atkPct: "攻击力百分比",
        def: "防御力",
        defPct: "防御力百分比",
        critRate: "暴击率",
        critDmg: "暴击伤害",
        anomalyProficiency: "异常精通",
        anomalyMastery: "异常掌控",
        penRate: "穿透率",
        penFlat: "穿透值",
        physicalDmgBonus: "属性伤害加成",
        fireDmgBonus: "属性伤害加成",
        iceDmgBonus: "属性伤害加成",
        electricDmgBonus: "属性伤害加成",
        etherDmgBonus: "属性伤害加成",
        windDmgBonus: "属性伤害加成",
        energyRegen: "能量自动回复"
    };
    const subStatKeys = {
        hp: "hp_flat",
        hpPct: "hp_pct",
        atk: "atk_flat",
        atkPct: "atk_pct",
        def: "def_flat",
        defPct: "def_pct",
        critRate: "crit_rate",
        critDmg: "crit_dmg",
        anomalyProficiency: "anomaly_prof",
        penFlat: "pen_flat"
    };

    const builds = imported.builds
        .filter(build => build && build.character && build.character.id)
        .map(build => {
            const globalSubStats = {
                atk_pct: 0,
                crit_rate: 0,
                crit_dmg: 0,
                hp_pct: 0,
                def_pct: 0,
                atk_flat: 0,
                def_flat: 0,
                hp_flat: 0,
                pen_flat: 0,
                anomaly_prof: 0
            };

            const importedDiscs = build.driveDiscs || [];
            const mappedDriveDiscs = importedDiscs.map(disc => {
                const mainStat = disc.mainStats && disc.mainStats[0];
                const mainStatKey = mainStat && (mainStat.key || "");
                const subStats = (disc.subStats || []).map(stat => {
                    const key = subStatKeys[stat.key];
                    if (key) {
                        const unit = S_SUBSTAT_VALUES[key];
                        const value = Number(stat.value);
                        if (unit && Number.isFinite(value)) {
                            globalSubStats[key] += Math.round(value / unit);
                        }
                    }
                    return {
                        type: key || "none",
                        rolls: 0
                    };
                });
                return {
                    setId: disc.setId || "",
                    mainStat: mainStatNames[mainStatKey] || "",
                    subStats
                };
            });
            const driveDiscBySlot = new Map(mappedDriveDiscs.map((disc, index) => [
                Number(importedDiscs[index]?.slot) || index + 1,
                disc,
            ]));
            // Legacy UI edits six fixed partitions. Missing UID discs are represented by
            // empty partitions rather than fabricating equipment or shortening the array.
            const driveDiscs = Array.from({ length: 6 }, (_, index) =>
                driveDiscBySlot.get(index + 1) || { setId: "", mainStat: "", subStats: [] }
            );

            return {
                characterId: String(build.character.id),
                level: Number(build.character.level) || 60,
                cinema: Number(build.character.cinema) || 0,
                coreRank: Number(build.character.coreLevel) || 0,
                weaponId: build.weapon ? String(build.weapon.id) : "",
                weaponRefinement: build.weapon ? Number(build.weapon.refinement) || 1 : 1,
                weaponPassiveActive: true,
                driveDiscs,
                globalSubStats,
                // 只作为导入审查依据保存，不参与计算；计算仍从角色/音擎/驱动盘结构重建面板。
                importedSource: build.source || imported.uid ? "miyoushe" : undefined,
                reportedPanel: build.reportedPanel || []
            };
        });

    if (builds.length === 0) return null;
    const currentIds = Array.isArray(squad)
        ? squad.filter(Boolean).map(member => String(member.characterId))
        : [];
    const preferredBuilds = currentIds
        .map(id => builds.find(build => build.characterId === id))
        .filter(Boolean);
    const selectedBuilds = [...preferredBuilds];
    return {
        // 如果页面已有小队，则按当前小队角色替换为米游社版本；空页面不擅自
        // 猜测用户要哪三名角色，完整账号构筑会交给角色卡点击/拖拽来选择。
        squad: [selectedBuilds[0] || null, selectedBuilds[1] || null, selectedBuilds[2] || null],
        accountBuilds: builds,
        activeSlotIndex: 0,
        activeSkillCategory: "chain",
        activeSkillLevel: "lv12",
        stunnedState: false,
        targetMonsterId: targetMonsterId || "",
        targetMonsterLevel,
        activeBuffsState: {}
    };
}

function exportConfig() {
    const configData = {
        squad,
        activeSlotIndex,
        activeSkillCategory,
        activeSkillLevel,
        stunnedState,
        targetMonsterId,
        targetMonsterLevel,
        activeBuffsState,
        selectedCrisisBuffs: Array.from(selectedCrisisBuffs),
        bossFieldCritDmgStacks,
        bossStunBaseValue: document.getElementById("input-boss-stun-base") ? parseFloat(document.getElementById("input-boss-stun-base").value) : 50
    };
    
    try {
        const jsonStr = JSON.stringify(configData, null, 2);
        const blob = new Blob([jsonStr], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        
        // Generate beautiful filename
        const now = new Date();
        const dateStr = now.toISOString().slice(0, 10);
        const timeStr = now.toTimeString().slice(0, 8).replace(/:/g, "-");
        a.download = `zzz_squad_config_${dateStr}_${timeStr}.json`;
        
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (err) {
        alert("❌ 导出配置文件失败：" + err.message);
    }
}

function importConfig() {
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = ".json";
    
    fileInput.onchange = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const rawConfigData = JSON.parse(event.target.result);
                const configData = mapMiyousheBuildsToLegacySquadConfig(rawConfigData) || rawConfigData;
                if (!configData || !configData.squad) throw new Error("无效的配置数据结构");

                importedAccountBuilds = Array.isArray(configData.accountBuilds)
                    ? configData.accountBuilds
                    : [];
                
                squad = configData.squad;
                activeSlotIndex = configData.activeSlotIndex !== undefined ? configData.activeSlotIndex : 0;
                activeSkillCategory = configData.activeSkillCategory || "basic";
                activeSkillLevel = configData.activeSkillLevel || "lv12";
                stunnedState = configData.stunnedState !== undefined ? configData.stunnedState : false;
                targetMonsterId = configData.targetMonsterId || "";
                targetMonsterLevel = configData.targetMonsterLevel || 70;
                activeBuffsState = configData.activeBuffsState || {};
                
                let crisisBuffs = configData.selectedCrisisBuffs;
                if (crisisBuffs && typeof crisisBuffs === "object" && !Array.isArray(crisisBuffs)) {
                    selectedCrisisBuffs = new Set();
                } else {
                    selectedCrisisBuffs = new Set(crisisBuffs || []);
                }
                
                bossFieldCritDmgStacks = configData.bossFieldCritDmgStacks !== undefined ? configData.bossFieldCritDmgStacks : 0;
                
                // Sync static/dynamic DOM inputs
                const chkStun = document.getElementById("chk-stunned-state");
                if (chkStun) chkStun.checked = stunnedState;
                
                const selBoss = document.getElementById("select-target-boss");
                if (selBoss) selBoss.value = targetMonsterId;
                
                const sliderLvl = document.getElementById("input-target-level");
                if (sliderLvl) {
                    sliderLvl.value = targetMonsterLevel;
                    const bossLevelLabel = document.getElementById("lbl-target-level");
                    if (bossLevelLabel) bossLevelLabel.textContent = `Lv.${targetMonsterLevel}`;
                }
                
                const bossStunBaseInput = document.getElementById("input-boss-stun-base");
                if (bossStunBaseInput && configData.bossStunBaseValue !== undefined) {
                    bossStunBaseInput.value = configData.bossStunBaseValue;
                }
                
                // Sync Skill Level
                const selectSkillLvl = document.getElementById("select-skill-level");
                if (selectSkillLvl) selectSkillLvl.value = activeSkillLevel;

                // Sync Skill Category Nav buttons
                const catNavs = document.querySelectorAll("#skill-tabs-category .skill-tab-btn");
                catNavs.forEach(btn => {
                    if (btn.dataset.cat === activeSkillCategory) {
                        btn.classList.add("active");
                    } else {
                        btn.classList.remove("active");
                    }
                });
                
                // Trigger W-Engine dropdown build and grid highlight if squad is configured
                const activeChar = squad[activeSlotIndex];
                if (activeChar) {
                    populateWeaponSelectForActive();
                    updateWeaponRosterActiveHighlights();
                }
                
                updateUI();
                alert("⚡ 配置已成功导入并刷新！");
            } catch (err) {
                alert("❌ 导入失败，文件格式不正确或已损坏：" + err.message);
            }
        };
        reader.readAsText(file);
    };
    
    fileInput.click();
}
