export type InjuryState = { error: string | null; message: string | null };

export const EMPTY_INJURY_STATE: InjuryState = { error: null, message: null };

/** الحد نفسه المضبوط في الخادم (`MAX_UPLOAD_MB`) — يُرفض الملف الأكبر قبل رفعه بلا داعٍ. */
export const MAX_UPLOAD_MB = 10;
