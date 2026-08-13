import { getRequestConfig } from "next-intl/server";

import { TIME_ZONE } from "./config";
import { messagesFor } from "./messages";
import { readLocale } from "@/lib/preferences";

export default getRequestConfig(async () => {
  const locale = await readLocale();
  return { locale, timeZone: TIME_ZONE, messages: messagesFor(locale) };
});
