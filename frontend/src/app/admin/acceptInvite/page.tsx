import { Suspense } from "react";
import AcceptInviteClient from "./acceptInviteClient";

export default function AcceptInvitePage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-black text-white grid place-items-center">
          Checking invite...
        </div>
      }
    >
      <AcceptInviteClient />
    </Suspense>
  );
}