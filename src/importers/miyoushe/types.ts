export interface MiyousheProperty {
  property_name?: string;
  property_id: number;
  base: string;
  add?: number | string;
  level?: number;
}

export interface MiyoushePanelProperty {
  property_name?: string;
  property_id: number;
  base?: string;
  add?: string;
  final_val: string;
}

export interface MiyousheEquip {
  id: number;
  level: number;
  rarity?: string;
  equipment_type: number;
  properties?: MiyousheProperty[];
  main_properties?: MiyousheProperty[];
  equip_suit?: { suit_id?: number };
}

export interface MiyousheAvatarDetail {
  avatar: {
    id: number;
    level: number;
    promotes?: number;
    rank?: number;
    properties?: MiyoushePanelProperty[];
    skills?: Array<{ level: number; skill_type: number }>;
  };
  weapon?: {
    id: number;
    level: number;
    star?: number;
  } | null;
  equip?: MiyousheEquip[];
}

export interface MiyousheDetailResponse {
  retcode: number;
  message?: string;
  data?: { list?: MiyousheAvatarDetail[] };
}
