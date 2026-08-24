export interface EnkaStat {
  PropertyId: number;
  PropertyValue: number;
  PropertyLevel?: number;
}

export interface EnkaEquipment {
  Uid?: number | string;
  Id: number;
  Level: number;
  BreakLevel?: number;
  MainStatList?: EnkaStat[];
  MainPropertyList?: EnkaStat[];
  RandomPropertyList?: EnkaStat[];
}

export interface EnkaEquippedItem {
  Slot: number;
  Equipment: EnkaEquipment;
}

export interface EnkaWeapon {
  Uid?: number | string;
  Id: number;
  Level: number;
  BreakLevel?: number;
  UpgradeLevel?: number;
}

export interface EnkaSkillLevel {
  Index?: number;
  Level?: number;
  SkillType?: number;
  SkillLevel?: number;
}

export interface EnkaAvatar {
  Id: number;
  Level: number;
  PromotionLevel?: number;
  TalentLevel?: number;
  CoreSkillEnhancement?: number;
  SkillLevelList?: EnkaSkillLevel[] | Record<string, number>;
  Weapon?: EnkaWeapon;
  EquippedList?: EnkaEquippedItem[];
}

export interface EnkaResponse {
  uid?: string | number;
  ttl?: number;
  PlayerInfo?: {
    SocialDetail?: {
      ProfileDetail?: {
        Nickname?: string;
      };
    };
    ShowcaseDetail?: {
      AvatarList?: EnkaAvatar[];
    };
  };
}

