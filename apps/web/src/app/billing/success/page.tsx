"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, Clock, AlertTriangle } from "lucide-react";
import Link from "next/link";
import { getToken } from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function BillingSuccessInner() {
  const searchParams = useSearchParams();
  const collectionStatus = searchParams.get("collection_status");
  const [countdown, setCountdown] = useState(5);

  useEffect(() => {
    // Refresh user plan data
    const token = getToken();
    if (token) {
      fetch(`${API_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      }).catch(() => {});
    }
  }, []);

  useEffect(() => {
    if (collectionStatus === "pending") return; // Don't auto-redirect on pending
    const timer = setInterval(() => {
      setCountdown((c) => {
        if (c <= 1) {
          window.location.href = "/";
          return 0;
        }
        return c - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [collectionStatus]);

  const isPending = collectionStatus === "pending";
  const isRejected = collectionStatus === "rejected";

  if (isRejected) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0A0A0F] p-4">
        <div className="text-center max-w-md">
          <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-white mb-2">Pago rechazado</h1>
          <p className="text-gray-400 mb-6">El pago no pudo ser procesado. Intentá con otro método de pago.</p>
          <Link href="/billing" className="px-6 py-3 bg-[#EAB308] text-black font-semibold rounded-lg hover:bg-[#D4A00A]">
            Volver a planes
          </Link>
        </div>
      </div>
    );
  }

  if (isPending) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0A0A0F] p-4">
        <div className="text-center max-w-md">
          <Clock className="w-16 h-16 text-amber-400 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-white mb-2">Pago pendiente</h1>
          <p className="text-gray-400 mb-6">Tu pago está siendo procesado. Te notificaremos por email cuando se confirme.</p>
          <Link href="/" className="px-6 py-3 bg-[#EAB308] text-black font-semibold rounded-lg hover:bg-[#D4A00A]">
            Ir al dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0A0A0F] p-4">
      <div className="text-center max-w-md">
        <CheckCircle2 className="w-16 h-16 text-green-400 mx-auto mb-4" />
        <h1 className="text-2xl font-bold text-white mb-2">¡Pago exitoso!</h1>
        <p className="text-gray-400 mb-2">Tu plan fue actualizado correctamente. Ya podés disfrutar de todas las funcionalidades.</p>
        <p className="text-gray-500 text-sm mb-6">Recibirás un email con la confirmación de tu pago.</p>
        <Link href="/" className="px-6 py-3 bg-[#EAB308] text-black font-semibold rounded-lg hover:bg-[#D4A00A]">
          Ir al dashboard
        </Link>
        <p className="text-gray-600 text-xs mt-4">Redirigiendo en {countdown}s...</p>
      </div>
    </div>
  );
}

export default function BillingSuccessPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-[#0A0A0F]">
        <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <BillingSuccessInner />
    </Suspense>
  );
}
