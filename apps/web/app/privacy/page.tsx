export default function PrivacyPage() {
  return (
    <main style={{ minHeight: '100vh', background: '#0b1220', color: '#e8eefc', padding: 24 }}>
      <div style={{ maxWidth: 860, margin: '0 auto', lineHeight: 1.65 }}>
        <h1>Privacy Policy</h1>
        <p><b>Effective date:</b> March 1, 2026</p>
        <p>
          DemandOrchestrator (operated by CrossCurrent Ventures LLC) provides content workflow tooling for drafting,
          scheduling, and publishing. This Privacy Policy explains what information we collect, how we use it, and your choices.
        </p>

        <h2>1. Information We Collect</h2>
        <ul>
          <li>Account information (name, email, workspace metadata)</li>
          <li>Content inputs you provide (ideas, uploaded files, prompts, drafts)</li>
          <li>Connected platform metadata (OAuth connection status and scoped tokens)</li>
          <li>Usage and operational logs (actions, timestamps, errors, publish statuses)</li>
        </ul>

        <h2>2. How We Use Information</h2>
        <ul>
          <li>Provide and operate the service</li>
          <li>Generate, schedule, and publish content according to your settings</li>
          <li>Maintain security, prevent abuse, and enforce policy guardrails</li>
          <li>Improve reliability and product performance</li>
        </ul>

        <h2>3. OAuth and Connected Accounts</h2>
        <p>
          We use OAuth to connect supported third-party platforms. We do <b>not</b> store your platform passwords.
          Access is limited by granted scopes and can be revoked by disconnecting your account.
        </p>

        <h2>4. Data Sharing</h2>
        <p>
          We do not sell personal data. We share information only with service providers required to operate the platform
          (e.g., hosting, model, and delivery providers), subject to contractual safeguards.
        </p>

        <h2>5. Data Retention</h2>
        <p>
          We retain data for as long as needed to provide the service, maintain records, and satisfy legal obligations.
          You may request deletion of your account data, subject to required retention exceptions.
        </p>

        <h2>6. Security</h2>
        <p>
          We use reasonable administrative and technical safeguards to protect your data. No method of transmission or storage
          is guaranteed 100% secure.
        </p>

        <h2>7. Your Choices</h2>
        <ul>
          <li>Disconnect linked accounts at any time</li>
          <li>Request data export or deletion</li>
          <li>Control posting approvals and automation settings</li>
        </ul>

        <h2>8. Children</h2>
        <p>The service is not intended for children under 13.</p>

        <h2>9. Changes</h2>
        <p>We may update this policy from time to time. Material changes will be reflected by updating the effective date.</p>

        <h2>10. Contact</h2>
        <p>
          CrossCurrent Ventures LLC<br />
          Email: jmetz776@gmail.com
        </p>
      </div>
    </main>
  );
}
