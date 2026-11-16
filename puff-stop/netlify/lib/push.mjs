import webpush from "web-push";
import { getStore } from "@netlify/blobs";

export const store = () => getStore({ name: "puffstop", consistency: "strong" });

export function push() {
  webpush.setVapidDetails(
    process.env.VAPID_SUBJECT || "https://example.com",
    process.env.VAPID_PUBLIC,
    process.env.VAPID_PRIVATE
  );
  return webpush;
}
export const backupStore = () => getStore({ name: "puffstop-backup", consistency: "strong" });
