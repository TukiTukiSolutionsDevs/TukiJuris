export default function DesignSystemPage() {
  return (
    <div style={{ background: "#0A0A0F", color: "#F5F5F5", minHeight: "100vh", fontFamily: "Inter, sans-serif" }}>
      {/* Header */}
      <header style={{ borderBottom: "1px solid #1E1E2A", padding: "24px 48px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div style={{ width: 40, height: 40, borderRadius: "8px", background: "#EAB308", display: "flex", alignItems: "center", justifyContent: "center", color: "#0A0A0F", fontWeight: 700, fontSize: 18 }}>T</div>
          <div>
            <h1 style={{ fontFamily: "DM Sans, Inter, sans-serif", fontSize: 32, fontWeight: 700, lineHeight: 1.2, margin: 0 }}>
              TukiJuris <span style={{ color: "#EAB308" }}>Design System</span>
            </h1>
            <p style={{ color: "#9CA3AF", fontSize: 14, margin: 0 }}>Fase 0 — Fundacion Visual v1.0.0-beta</p>
          </div>
        </div>
      </header>

      <main style={{ maxWidth: 1200, margin: "0 auto", padding: "48px 24px" }}>

        {/* ==================== PALETA DE COLORES ==================== */}
        <Section title="1. Paleta de Colores">

          {/* Brand del Logo */}
          <SubSection title="Colores del Logo">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 16 }}>
              <ColorSwatch hex="#2C3E50" name="Navy" label="Traje tucan" role="Superficies, nav" />
              <ColorSwatch hex="#EAB308" name="Gold" label="Pico/Balanza" role="Primary CTA, badges" />
              <ColorSwatch hex="#B91C1C" name="Rojo" label="Corbata" role="Alertas, errores" />
              <ColorSwatch hex="#1A1A1A" name="Negro" label="Cuerpo tucan" role="Fondos profundos" />
              <ColorSwatch hex="#FFFFFF" name="Blanco" label="Pecho tucan" role="Texto principal" dark />
            </div>
          </SubSection>

          {/* Fondos */}
          <SubSection title="Fondos (Dark Mode)">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
              <ColorSwatch hex="#0A0A0F" name="bg-base" role="Fondo principal" />
              <ColorSwatch hex="#111116" name="bg-surface" role="Cards, modales" />
              <ColorSwatch hex="#1A1A22" name="bg-surface-raised" role="Cards elevadas, sidebar" />
              <ColorSwatch hex="#22222E" name="bg-surface-overlay" role="Dropdowns, popovers" />
            </div>
          </SubSection>

          {/* Bordes */}
          <SubSection title="Bordes">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
              <ColorSwatch hex="#1E1E2A" name="border-subtle" role="Entre secciones" />
              <ColorSwatch hex="#2A2A35" name="border-default" role="Inputs, cards" />
              <ColorSwatch hex="#3A3A48" name="border-strong" role="Activos, hover" />
            </div>
          </SubSection>

          {/* Texto */}
          <SubSection title="Texto">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
              <ColorSwatch hex="#F5F5F5" name="text-primary" role="Texto principal" dark />
              <ColorSwatch hex="#9CA3AF" name="text-secondary" role="Labels, auxiliar" dark />
              <ColorSwatch hex="#6B7280" name="text-muted" role="Placeholders, hints" />
              <ColorSwatch hex="#4B5563" name="text-disabled" role="Deshabilitado" />
            </div>
          </SubSection>

          {/* Brand / Accent */}
          <SubSection title="Brand / Accent">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
              <ColorSwatch hex="#EAB308" name="brand-primary" role="CTAs, links activos" />
              <ColorSwatch hex="#D4A00A" name="brand-primary-hover" role="Hover CTAs" />
              <ColorSwatch hex="#2C3E50" name="brand-secondary" role="Cards, nav selected" />
              <ColorSwatch hex="#34495E" name="brand-navy-light" role="Hover navy" />
            </div>
          </SubSection>

          {/* Semanticos */}
          <SubSection title="Semanticos">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
              <ColorSwatch hex="#34D399" name="success" role="Confirmaciones" />
              <ColorSwatch hex="#F87171" name="error" role="Errores, validacion" />
              <ColorSwatch hex="#FBBF24" name="warning" role="Warnings" />
              <ColorSwatch hex="#60A5FA" name="info" role="Info, tips" />
            </div>
          </SubSection>

          {/* Plan Badges */}
          <SubSection title="Plan Badges">
            <div style={{ display: "flex", gap: 16 }}>
              <PlanBadge plan="Free/Beta" bgColor="#6B728020" textColor="#9CA3AF" />
              <PlanBadge plan="Base" bgColor="#EAB30820" textColor="#EAB308" />
              <PlanBadge plan="Enterprise" bgColor="#A78BFA20" textColor="#A78BFA" />
            </div>
          </SubSection>
        </Section>

        {/* ==================== TIPOGRAFIA ==================== */}
        <Section title="2. Tipografia">
          <SubSection title="Familias">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 24 }}>
              <FontCard family="DM Sans, sans-serif" name="DM Sans" weight="Bold (700)" usage="Headlines, hero text" sample="Consulta Legal IA" />
              <FontCard family="Inter, sans-serif" name="Inter" weight="Regular (400) / Semibold (600)" usage="Body, labels, botones" sample="Plataforma juridica inteligente" />
              <FontCard family="Geist Mono, monospace" name="Geist Mono" weight="Regular" usage="Code blocks, API docs" sample="Bearer eyJhbGc..." />
            </div>
          </SubSection>

          <SubSection title="Escala Tipografica">
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <TypeScale level="display" size="48px" lh="1.1" family="DM Sans, sans-serif" weight={700} usage="Hero heading" />
              <TypeScale level="h1" size="32px" lh="1.2" family="DM Sans, sans-serif" weight={700} usage="Page titles" />
              <TypeScale level="h2" size="24px" lh="1.3" family="DM Sans, sans-serif" weight={700} usage="Section headings" />
              <TypeScale level="h3" size="20px" lh="1.4" family="DM Sans, sans-serif" weight={700} usage="Card titles" />
              <TypeScale level="h4" size="16px" lh="1.5" family="Inter, sans-serif" weight={600} usage="Subsections" />
              <TypeScale level="body-lg" size="16px" lh="1.6" family="Inter, sans-serif" weight={400} usage="Body emphasis" />
              <TypeScale level="body" size="14px" lh="1.6" family="Inter, sans-serif" weight={400} usage="Default body" />
              <TypeScale level="body-sm" size="13px" lh="1.5" family="Inter, sans-serif" weight={400} usage="Secondary text" />
              <TypeScale level="caption" size="12px" lh="1.4" family="Inter, sans-serif" weight={400} usage="Labels, hints" />
              <TypeScale level="micro" size="10px" lh="1.3" family="Inter, sans-serif" weight={400} usage="Tags, badges" />
            </div>
          </SubSection>
        </Section>

        {/* ==================== ESPACIADO ==================== */}
        <Section title="3. Espaciado">
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {[
              { token: "xs", value: 4, usage: "Padding minimo, gaps tight" },
              { token: "sm", value: 8, usage: "Badges, gaps menores" },
              { token: "md", value: 12, usage: "Botones, inputs" },
              { token: "lg", value: 16, usage: "Cards, secciones" },
              { token: "xl", value: 24, usage: "Margin entre secciones" },
              { token: "2xl", value: 32, usage: "Margin bloques grandes" },
              { token: "3xl", value: 48, usage: "Hero, separadores" },
              { token: "4xl", value: 64, usage: "Margin de pagina" },
            ].map((s) => (
              <div key={s.token} style={{ display: "flex", alignItems: "center", gap: 16 }}>
                <span style={{ width: 40, fontSize: 13, color: "#9CA3AF", fontFamily: "Geist Mono, monospace", textAlign: "right" }}>{s.token}</span>
                <span style={{ width: 50, fontSize: 12, color: "#6B7280", fontFamily: "Geist Mono, monospace" }}>{s.value}px</span>
                <div style={{ width: s.value, height: 24, background: "#EAB308", borderRadius: 4, minWidth: 4 }} />
                <span style={{ fontSize: 13, color: "#6B7280" }}>{s.usage}</span>
              </div>
            ))}
          </div>
        </Section>

        {/* ==================== BORDES Y SOMBRAS ==================== */}
        <Section title="4. Bordes y Sombras">
          <SubSection title="Border Radius">
            <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
              {[
                { token: "radius-sm", value: 6, label: "Badges, tags" },
                { token: "radius-md", value: 8, label: "Botones, inputs" },
                { token: "radius-lg", value: 12, label: "Cards, modales" },
                { token: "radius-xl", value: 16, label: "Containers" },
                { token: "radius-full", value: 9999, label: "Avatares, pills" },
              ].map((r) => (
                <div key={r.token} style={{ textAlign: "center" }}>
                  <div style={{
                    width: 64, height: 64,
                    background: "#1A1A22",
                    border: "2px solid #2A2A35",
                    borderRadius: r.value,
                    margin: "0 auto 8px",
                  }} />
                  <div style={{ fontSize: 12, fontFamily: "Geist Mono, monospace", color: "#EAB308" }}>{r.value === 9999 ? "full" : `${r.value}px`}</div>
                  <div style={{ fontSize: 11, color: "#6B7280" }}>{r.token}</div>
                  <div style={{ fontSize: 11, color: "#4B5563" }}>{r.label}</div>
                </div>
              ))}
            </div>
          </SubSection>

          <SubSection title="Sombras">
            <div style={{ display: "flex", gap: 32 }}>
              {[
                { token: "shadow-sm", value: "0 1px 2px #00000020", label: "Inputs focus" },
                { token: "shadow-md", value: "0 4px 12px #00000030", label: "Cards hover" },
                { token: "shadow-lg", value: "0 8px 24px #00000040", label: "Modales, dropdowns" },
              ].map((s) => (
                <div key={s.token} style={{ textAlign: "center" }}>
                  <div style={{
                    width: 120, height: 80,
                    background: "#111116",
                    border: "1px solid #1E1E2A",
                    borderRadius: 12,
                    boxShadow: s.value,
                    margin: "0 auto 8px",
                  }} />
                  <div style={{ fontSize: 12, fontFamily: "Geist Mono, monospace", color: "#EAB308" }}>{s.token}</div>
                  <div style={{ fontSize: 11, color: "#6B7280" }}>{s.label}</div>
                </div>
              ))}
            </div>
          </SubSection>
        </Section>

        {/* ==================== COMPONENTES BASE ==================== */}
        <Section title="5. Componentes Base">

          {/* Botones */}
          <SubSection title="Botones">
            <div style={{ display: "flex", gap: 16, flexWrap: "wrap", alignItems: "center" }}>
              <Button variant="primary">Consultar Ahora</Button>
              <Button variant="secondary">Ver Detalles</Button>
              <Button variant="ghost">Cancelar</Button>
              <Button variant="danger">Eliminar</Button>
              <Button variant="navy">Nav Activo</Button>
            </div>
            <div style={{ marginTop: 24 }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #1E1E2A" }}>
                    {["Variante", "Fondo", "Texto", "Borde", "Uso"].map(h => (
                      <th key={h} style={{ textAlign: "left", padding: "8px 12px", color: "#9CA3AF", fontWeight: 600 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody style={{ fontFamily: "Geist Mono, monospace", fontSize: 12 }}>
                  {[
                    ["Primary", "#EAB308", "#0A0A0F", "none", "CTA principal"],
                    ["Secondary", "transparent", "#F5F5F5", "#2A2A35", "Acciones secundarias"],
                    ["Ghost", "transparent", "#9CA3AF", "none", "Acciones terciarias"],
                    ["Danger", "#F8717120", "#F87171", "none", "Eliminar, cancelar"],
                    ["Navy", "#2C3E50", "#F5F5F5", "none", "Nav items activos"],
                  ].map(([v, bg, txt, brd, uso]) => (
                    <tr key={v} style={{ borderBottom: "1px solid #1E1E2A" }}>
                      <td style={{ padding: "8px 12px", color: "#F5F5F5" }}>{v}</td>
                      <td style={{ padding: "8px 12px", color: "#EAB308" }}>{bg}</td>
                      <td style={{ padding: "8px 12px", color: "#9CA3AF" }}>{txt}</td>
                      <td style={{ padding: "8px 12px", color: "#9CA3AF" }}>{brd}</td>
                      <td style={{ padding: "8px 12px", color: "#6B7280", fontFamily: "Inter, sans-serif" }}>{uso}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SubSection>

          {/* Inputs */}
          <SubSection title="Inputs">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 24 }}>
              <div>
                <label style={{ fontSize: 13, color: "#9CA3AF", marginBottom: 6, display: "block" }}>Default</label>
                <div style={{
                  background: "#111116",
                  border: "1px solid #2A2A35",
                  borderRadius: 8,
                  padding: "12px 16px",
                  height: 44,
                  display: "flex",
                  alignItems: "center",
                  color: "#6B7280",
                  fontSize: 14,
                  boxSizing: "border-box",
                }}>
                  Ingresa tu consulta legal...
                </div>
                <div style={{ marginTop: 6, fontFamily: "Geist Mono, monospace", fontSize: 11, color: "#4B5563" }}>
                  bg: #111116 | border: #2A2A35 | radius: 8px | h: 44px
                </div>
              </div>
              <div>
                <label style={{ fontSize: 13, color: "#9CA3AF", marginBottom: 6, display: "block" }}>Focus</label>
                <div style={{
                  background: "#111116",
                  border: "1px solid #EAB308",
                  borderRadius: 8,
                  padding: "12px 16px",
                  height: 44,
                  display: "flex",
                  alignItems: "center",
                  color: "#F5F5F5",
                  fontSize: 14,
                  boxShadow: "0 1px 2px #00000020",
                  boxSizing: "border-box",
                }}>
                  Derecho laboral Peru
                </div>
                <div style={{ marginTop: 6, fontFamily: "Geist Mono, monospace", fontSize: 11, color: "#4B5563" }}>
                  border: #EAB308 | shadow: shadow-sm
                </div>
              </div>
            </div>
          </SubSection>

          {/* Cards */}
          <SubSection title="Cards">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 24 }}>
              <Card title="Default" description="Estado base de una card. Fondo surface con borde sutil." />
              <Card title="Hover" description="Al pasar el mouse. Borde mas visible y sombra media." hover />
              <Card title="Con Accent Navy" description="Card destacada con fondo navy para items seleccionados." navy />
            </div>
            <div style={{ marginTop: 16, fontFamily: "Geist Mono, monospace", fontSize: 11, color: "#4B5563" }}>
              bg: #111116 | border: #1E1E2A | radius: 12px | padding: 20px | hover: border #2A2A35 + shadow-md
            </div>
          </SubSection>
        </Section>

        {/* ==================== REGLAS ==================== */}
        <Section title="6. Reglas de Diseno">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32 }}>
            <div>
              <h4 style={{ color: "#34D399", fontSize: 16, fontWeight: 600, marginBottom: 12 }}>DO</h4>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 8 }}>
                {[
                  "Dark mode como base en TODAS las pantallas",
                  "Gold #EAB308 como accent principal",
                  "Navy #2C3E50 como accent secundario",
                  "Respetar spacing system (no valores arbitrarios)",
                  "Inputs y botones: 44px altura minima",
                  "Feedback visual en toda interaccion",
                ].map((r, i) => (
                  <li key={i} style={{ fontSize: 13, color: "#9CA3AF", display: "flex", gap: 8 }}>
                    <span style={{ color: "#34D399" }}>&#10003;</span> {r}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 style={{ color: "#F87171", fontSize: 16, fontWeight: 600, marginBottom: 12 }}>DON&apos;T</h4>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 8 }}>
                {[
                  "Rojo como color primario (solo errores)",
                  "Fondos blancos puros (#FFF como bg)",
                  "Mezclar border-radius arbitrariamente",
                  "Mas de 2 fuentes (DM Sans + Inter)",
                  "Animaciones que bloqueen interaccion",
                  "Cambiar estructura de endpoints/API",
                ].map((r, i) => (
                  <li key={i} style={{ fontSize: 13, color: "#9CA3AF", display: "flex", gap: 8 }}>
                    <span style={{ color: "#F87171" }}>&#10007;</span> {r}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </Section>

        {/* Footer */}
        <div style={{ borderTop: "1px solid #1E1E2A", marginTop: 64, paddingTop: 24, textAlign: "center" }}>
          <p style={{ color: "#4B5563", fontSize: 12 }}>
            TukiJuris Design System v1.0.0-beta — Fase 0 Fundacion — Pendiente aprobacion
          </p>
        </div>
      </main>
    </div>
  );
}

/* ==================== SUB-COMPONENTS ==================== */

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section style={{ marginBottom: 64 }}>
      <h2 style={{
        fontFamily: "DM Sans, sans-serif",
        fontSize: 24,
        fontWeight: 700,
        lineHeight: 1.3,
        marginBottom: 32,
        paddingBottom: 12,
        borderBottom: "1px solid #1E1E2A",
      }}>
        {title}
      </h2>
      {children}
    </section>
  );
}

function SubSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 32 }}>
      <h3 style={{ fontSize: 16, fontWeight: 600, color: "#9CA3AF", marginBottom: 16 }}>{title}</h3>
      {children}
    </div>
  );
}

function ColorSwatch({ hex, name, label, role, dark }: { hex: string; name: string; label?: string; role: string; dark?: boolean }) {
  return (
    <div>
      <div style={{
        width: "100%",
        height: 72,
        background: hex,
        borderRadius: 8,
        border: dark ? "1px solid #2A2A35" : "none",
        marginBottom: 8,
      }} />
      <div style={{ fontFamily: "Geist Mono, monospace", fontSize: 12, color: "#EAB308" }}>{hex}</div>
      <div style={{ fontSize: 13, fontWeight: 600, color: "#F5F5F5" }}>{name}</div>
      {label && <div style={{ fontSize: 11, color: "#6B7280" }}>{label}</div>}
      <div style={{ fontSize: 11, color: "#4B5563" }}>{role}</div>
    </div>
  );
}

function PlanBadge({ plan, bgColor, textColor }: { plan: string; bgColor: string; textColor: string }) {
  return (
    <span style={{
      background: bgColor,
      color: textColor,
      padding: "4px 12px",
      borderRadius: 6,
      fontSize: 12,
      fontWeight: 600,
    }}>
      {plan}
    </span>
  );
}

function FontCard({ family, name, weight, usage, sample }: { family: string; name: string; weight: string; usage: string; sample: string }) {
  return (
    <div style={{
      background: "#111116",
      border: "1px solid #1E1E2A",
      borderRadius: 12,
      padding: 20,
    }}>
      <div style={{ fontFamily: family, fontSize: 28, fontWeight: 700, marginBottom: 12 }}>{sample}</div>
      <div style={{ fontSize: 14, fontWeight: 600, color: "#EAB308" }}>{name}</div>
      <div style={{ fontSize: 12, color: "#9CA3AF" }}>{weight}</div>
      <div style={{ fontSize: 12, color: "#6B7280" }}>{usage}</div>
    </div>
  );
}

function TypeScale({ level, size, lh, family, weight, usage }: { level: string; size: string; lh: string; family: string; weight: number; usage: string }) {
  return (
    <div style={{ display: "flex", alignItems: "baseline", gap: 16, borderBottom: "1px solid #1E1E2A", paddingBottom: 12 }}>
      <span style={{ width: 70, fontSize: 12, fontFamily: "Geist Mono, monospace", color: "#EAB308", flexShrink: 0 }}>{level}</span>
      <span style={{ width: 50, fontSize: 12, fontFamily: "Geist Mono, monospace", color: "#6B7280", flexShrink: 0 }}>{size}</span>
      <span style={{ fontFamily: family, fontSize: size, fontWeight: weight, lineHeight: lh, flex: 1 }}>
        TukiJuris Abogados
      </span>
      <span style={{ fontSize: 11, color: "#4B5563", flexShrink: 0 }}>{usage}</span>
    </div>
  );
}

function Button({ variant, children }: { variant: "primary" | "secondary" | "ghost" | "danger" | "navy"; children: React.ReactNode }) {
  const styles: Record<string, React.CSSProperties> = {
    primary: { background: "#EAB308", color: "#0A0A0F", border: "none" },
    secondary: { background: "transparent", color: "#F5F5F5", border: "1px solid #2A2A35" },
    ghost: { background: "transparent", color: "#9CA3AF", border: "none" },
    danger: { background: "#F8717120", color: "#F87171", border: "none" },
    navy: { background: "#2C3E50", color: "#F5F5F5", border: "none" },
  };

  return (
    <button style={{
      ...styles[variant],
      height: 44,
      padding: "0 24px",
      borderRadius: 8,
      fontSize: 14,
      fontWeight: 600,
      cursor: "pointer",
      fontFamily: "Inter, sans-serif",
    }}>
      {children}
    </button>
  );
}

function Card({ title, description, hover, navy }: { title: string; description: string; hover?: boolean; navy?: boolean }) {
  return (
    <div style={{
      background: navy ? "#2C3E50" : "#111116",
      border: `1px solid ${hover ? "#2A2A35" : "#1E1E2A"}`,
      borderRadius: 12,
      padding: 20,
      boxShadow: hover ? "0 4px 12px #00000030" : "none",
    }}>
      <h4 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, margin: "0 0 8px 0" }}>{title}</h4>
      <p style={{ fontSize: 13, color: "#9CA3AF", margin: 0, lineHeight: 1.5 }}>{description}</p>
    </div>
  );
}
