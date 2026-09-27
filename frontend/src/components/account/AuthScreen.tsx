"use client";

import { ArrowRight, LockKeyhole, Mail, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";

import { Link, useRouter } from "@/i18n/navigation";
import { browserApi, type ApiRequestError } from "@/lib/browser-api";

type Mode = "login" | "register" | "verify" | "reset" | "reset-code";

function errorText(error: unknown): string {
  const body = (error as ApiRequestError)?.body;
  if (!body) return "Не вдалося виконати запит. Спробуйте ще раз.";
  for (const value of Object.values(body)) {
    if (typeof value === "string") return value;
    if (Array.isArray(value) && typeof value[0] === "string") return value[0];
  }
  return "Не вдалося виконати запит. Спробуйте ще раз.";
}

export function AuthScreen({ oauthError = false }: { oauthError?: boolean }) {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(oauthError ? "Не вдалося увійти через провайдера. Спробуйте ще раз." : "");
  const [message, setMessage] = useState("");
  const [providers, setProviders] = useState({ google: false, apple: false });
  const [appleDevice] = useState(() => typeof navigator !== "undefined" && /iPhone|iPad|iPod|Macintosh/.test(navigator.userAgent));

  useEffect(() => {
    browserApi.accountConfig().then(setProviders).catch(() => undefined);
  }, []);

  const changeMode = (next: Mode) => { setMode(next); setError(""); setMessage(""); };
  const finish = () => { router.push("/account"); router.refresh(); };

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true); setError(""); setMessage("");
    try {
      if (mode === "register") {
        await browserApi.register({ email, password, first_name: firstName });
        changeMode("verify");
        setMessage("Надіслали шестизначний код на вашу пошту. Він діє 10 хвилин.");
      } else if (mode === "verify") {
        await browserApi.verifyEmail(email, code);
        finish();
      } else if (mode === "login") {
        await browserApi.login(email, password);
        finish();
      } else if (mode === "reset") {
        await browserApi.requestPasswordReset(email);
        changeMode("reset-code");
        setMessage("Якщо обліковий запис існує, на пошту надійшов код.");
      } else {
        await browserApi.confirmPasswordReset(email, code, password);
        finish();
      }
    } catch (caught) {
      if (mode === "login" && (caught as ApiRequestError)?.body?.email_verification_required) {
        changeMode("verify");
        setMessage("Підтвердіть адресу кодом із листа. Якщо код застарів, надішліть новий.");
      } else setError(errorText(caught));
    } finally { setBusy(false); }
  }

  const title = { login: "Вхід до кабінету", register: "Створити акаунт", verify: "Підтвердити email", reset: "Відновити пароль", "reset-code": "Новий пароль" }[mode];
  const field = "h-12 w-full rounded-xl border border-platinum-200 bg-white px-4 text-[15px] outline-none focus:border-gold-500 focus:ring-2 focus:ring-gold-500/20";

  return (
    <div className="mx-auto max-w-[1100px] px-4 py-12 sm:px-6 sm:py-20">
      <div className="grid overflow-hidden rounded-[28px] bg-white shadow-[0_25px_80px_-45px_rgba(20,22,24,.35)] ring-1 ring-platinum-200 md:grid-cols-[.9fr_1.1fr]">
        <div className="bg-ink px-8 py-10 text-white sm:px-12 sm:py-14">
          <span className="inline-flex items-center gap-2 rounded-full border border-gold-500/30 px-3 py-1 text-[11px] font-bold uppercase tracking-[.18em] text-gold-300"><ShieldCheck className="size-4" /> Premier Parts</span>
          <h1 className="mt-10 font-display text-[34px] leading-tight sm:text-[42px]">Ваші авто.<br />Ваші деталі.<br /><span className="text-gold-300">Ваш кабінет.</span></h1>
          <p className="mt-5 max-w-sm text-[15px] leading-7 text-platinum-300">Зберігайте свій автопарк, переглядайте покупки, відстежуйте замовлення та знаходьте сумісні запчастини швидше.</p>
          <Link href="/catalog" className="mt-10 inline-flex items-center gap-2 text-sm font-semibold text-gold-300 hover:text-white">Повернутися до каталогу <ArrowRight className="size-4" /></Link>
        </div>
        <div className="px-6 py-9 sm:px-12 sm:py-12">
          <div className="mb-7 flex gap-2 text-sm font-semibold">
            <button type="button" onClick={() => changeMode("login")} className={`rounded-xl px-4 py-2.5 ${mode === "login" ? "bg-ink text-white" : "text-platinum-500 hover:bg-platinum-50"}`}>Увійти</button>
            <button type="button" onClick={() => changeMode("register")} className={`rounded-xl px-4 py-2.5 ${mode === "register" ? "bg-ink text-white" : "text-platinum-500 hover:bg-platinum-50"}`}>Реєстрація</button>
          </div>
          <h2 className="font-display text-[27px] font-medium">{title}</h2>
          <p className="mt-1 text-[13px] text-platinum-500">{mode === "verify" ? `Код для ${email}` : mode === "register" ? "Вкажіть дані, щоб отримати код підтвердження." : "Ваші дані збережені та доступні лише вам."}</p>
          <form onSubmit={submit} className="mt-7 grid gap-4">
            {mode === "register" && <label className="grid gap-1.5 text-sm font-semibold">Ім’я<input className={field} autoComplete="given-name" value={firstName} onChange={(e) => setFirstName(e.target.value)} maxLength={150} /></label>}
            <label className="grid gap-1.5 text-sm font-semibold">Email<input className={field} type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required disabled={mode === "verify" || mode === "reset-code"} /></label>
            {(mode === "login" || mode === "register" || mode === "reset-code") && <label className="grid gap-1.5 text-sm font-semibold">Пароль<input className={field} type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} required /></label>}
            {(mode === "verify" || mode === "reset-code") && <label className="grid gap-1.5 text-sm font-semibold">Код із листа<input className={`${field} text-center font-mono text-xl tracking-[.3em]`} inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} required /></label>}
            {error && <p role="alert" className="rounded-xl bg-red-50 p-3 text-[13px] text-red-700">{error}</p>}
            {message && <p role="status" className="rounded-xl bg-emerald-50 p-3 text-[13px] text-emerald-800">{message}</p>}
            <button disabled={busy} type="submit" className="mt-1 flex h-12 items-center justify-center gap-2 rounded-xl bg-gold-400 font-bold text-ink transition hover:bg-gold-300 disabled:opacity-60">{busy ? "Зачекайте…" : mode === "login" ? "Увійти" : mode === "register" ? "Надіслати код" : mode === "verify" ? "Підтвердити" : mode === "reset" ? "Отримати код" : "Зберегти пароль"}<ArrowRight className="size-4" /></button>
          </form>
          {mode === "login" && <button type="button" onClick={() => changeMode("reset")} className="mt-4 text-[13px] font-semibold text-gold-700 hover:underline">Забули пароль?</button>}
          {mode === "verify" && <button type="button" onClick={async () => { try { await browserApi.resendEmail(email); setMessage("Новий код надіслано."); setError(""); } catch (caught) { setError(errorText(caught)); } }} className="mt-4 text-[13px] font-semibold text-gold-700 hover:underline">Надіслати код ще раз</button>}
          {mode === "reset-code" && <button type="button" onClick={() => changeMode("reset")} className="mt-4 text-[13px] font-semibold text-gold-700 hover:underline">Змінити email</button>}
          {(mode === "login" || mode === "register") && (providers.google || (providers.apple && appleDevice)) && <div className="mt-7 border-t border-platinum-200 pt-6"><p className="mb-4 text-center text-xs text-platinum-400">або продовжити через</p><div className="grid gap-2 sm:grid-cols-2">{providers.google && <button type="button" onClick={() => window.location.assign(new URL("/api/account/oauth/google/start", window.location.origin).href)} className="flex h-12 items-center justify-center gap-2 rounded-xl border border-platinum-200 font-semibold hover:bg-platinum-50"><Mail className="size-4" /> Google</button>}{providers.apple && appleDevice && <button type="button" onClick={() => window.location.assign(new URL("/api/account/oauth/apple/start", window.location.origin).href)} className="flex h-12 items-center justify-center gap-2 rounded-xl border border-platinum-200 font-semibold hover:bg-platinum-50"><LockKeyhole className="size-4" /> Apple</button>}</div></div>}
        </div>
      </div>
    </div>
  );
}
