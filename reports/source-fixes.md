# Spec source metadata to fix

Generated 2026-11-10 by `crawler/build_data.py` from https://openid.net/specs/. Regenerated on every crawl; an entry disappears once a corrected revision is published.

Until a fix is published, the dashboard uses `crawler/overrides.json`. Specs with an override are marked **(overridden)** below.

| Section | Count |
|---|---|
| [Wrong working group (fix in source)](#wrong-working-group-fix-in-source) | 4 |
| [Working group changed during the spec's history (confirm)](#working-group-changed-during-the-specs-history-confirm) | 4 |
| [Renames missing a redirect stub (add on openid.net)](#renames-missing-a-redirect-stub-add-on-openidnet) | 6 |
| [Working group not stated — active specs (add to source)](#working-group-not-stated--active-specs-add-to-source) | 2 |
| [Inconsistent working group names (harmonise)](#inconsistent-working-group-names-harmonise) | 12 |
| [Other metadata](#other-metadata) | 4 |
| [Working group not stated — historical specs (low priority)](#working-group-not-stated--historical-specs-low-priority) | 44 |

## Wrong working group (fix in source)

The document names a WG other than the one that owns the spec, at a time when the owning WG was already in use. Almost always a copied template.

| Spec | Revision(s) | Document says | Should be | Notes |
|---|---|---|---|---|
| FAPI 2.0 Attacker Model<br>`fapi-attacker-model-2_0` | [`fapi-2_0-attacker-model-00`](https://openid.net/specs/fapi-2_0-attacker-model-00.html)<br>[`fapi-2_0-attacker-model-01`](https://openid.net/specs/fapi-2_0-attacker-model-01.html)<br>[`fapi-2_0-attacker-model-ID1`](https://openid.net/specs/fapi-2_0-attacker-model-ID1.html) | connect | FAPI | States AB/Connect, but the FAPI WG was already labelling documents (first: openid-financial-api-part-2-wd-07, 2020-10-23). |
| FAPI 2.0 Security Profile<br>`fapi-security-profile-2_0` **(overridden)** | [`fapi-2_0-baseline-00`](https://openid.net/specs/fapi-2_0-baseline-00.html)<br>[`fapi-2_0-baseline-01`](https://openid.net/specs/fapi-2_0-baseline-01.html)<br>[`fapi-2_0-baseline-ID1`](https://openid.net/specs/fapi-2_0-baseline-ID1.html) | connect | FAPI | States AB/Connect, but the FAPI WG was already labelling documents (first: openid-financial-api-part-2-wd-07, 2020-10-23). |
| OpenID for Verifiable Credential Issuance 1.0<br>`openid-4-verifiable-credential-issuance-1_0` | [`openid-4-verifiable-credential-issuance-1_0-13`](https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0-13.html)<br>[`openid-4-verifiable-credential-issuance-1_0-ID1`](https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0-ID1.html) | OpenID Connect | Digital Credentials Protocols | States AB/Connect, but the Digital Credentials Protocols WG was already labelling documents (first: openid4vc-high-assurance-interoperability-profile-sd-jwt-vc-1_0-00, 2024-01-09). |
| OpenID for Verifiable Presentations 1.0<br>`openid-4-verifiable-presentations-1_0` | [`openid-4-verifiable-presentations-1_0-21`](https://openid.net/specs/openid-4-verifiable-presentations-1_0-21.html) … [`openid-4-verifiable-presentations-1_0-ID3`](https://openid.net/specs/openid-4-verifiable-presentations-1_0-ID3.html) (4 revisions) | OpenID Connect, connect | Digital Credentials Protocols | States AB/Connect, but the Digital Credentials Protocols WG was already labelling documents (first: openid4vc-high-assurance-interoperability-profile-sd-jwt-vc-1_0-00, 2024-01-09). |

## Working group changed during the spec's history (confirm)

Earlier revisions name another WG before the owning WG appears anywhere in the corpus. Usually a real hand-over between WGs; no fix needed if so.

| Spec | Revision(s) | Document says | Should be | Notes |
|---|---|---|---|---|
| OpenID for Verifiable Credential Issuance 1.0<br>`openid-4-verifiable-credential-issuance-1_0` | [`openid-connect-4-verifiable-credential-issuance-1_0-02`](https://openid.net/specs/openid-connect-4-verifiable-credential-issuance-1_0-02.html) … [`openid-4-verifiable-credential-issuance-1_0-12`](https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0-12.html) (8 revisions) | OpenID Connect, connect | Digital Credentials Protocols | States AB/Connect before any document named the Digital Credentials Protocols WG. Probably developed there before a hand-over; confirm and leave as-is if so. |
| OpenID for Verifiable Presentations 1.0<br>`openid-4-verifiable-presentations-1_0` | [`openid-connect-4-verifiable-presentations-1_0-00`](https://openid.net/specs/openid-connect-4-verifiable-presentations-1_0-00.html) … [`openid-4-verifiable-presentations-1_0-20`](https://openid.net/specs/openid-4-verifiable-presentations-1_0-20.html) (16 revisions) | connect | Digital Credentials Protocols | States AB/Connect before any document named the Digital Credentials Protocols WG. Probably developed there before a hand-over; confirm and leave as-is if so. |
| OpenID for Verifiable Presentations over BLE<br>`openid-4-verifiable-presentations-over-ble-1_0` | [`openid-4-verifiable-presentations-over-ble-1_0-00`](https://openid.net/specs/openid-4-verifiable-presentations-over-ble-1_0-00.html) | OpenID Connect | Digital Credentials Protocols | States AB/Connect before any document named the Digital Credentials Protocols WG. Probably developed there before a hand-over; confirm and leave as-is if so. Affects the latest approved document, or the latest draft if none has been approved. |
| OpenID Connect for Identity Assurance 1.0<br>`openid-connect-4-identity-assurance-1_0` | [`openid-connect-4-identity-assurance-00`](https://openid.net/specs/openid-connect-4-identity-assurance-00.html)<br>[`openid-connect-4-identity-assurance-1_0-09`](https://openid.net/specs/openid-connect-4-identity-assurance-1_0-09.html) | OpenID Foundation Artifact Binding Working Group, connect | eKYC & IDA | States AB/Connect before any document named the eKYC & IDA WG. Probably developed there before a hand-over; confirm and leave as-is if so. |

## Renames missing a redirect stub (add on openid.net)

Merged in the dashboard because the documents carry the same title, but the old URL has no "Renamed Specification" page pointing to the new one.

| Spec | Revision(s) | Document says | Should be | Notes |
|---|---|---|---|---|
| FAPI 2.0 Attacker Model<br>`fapi-attacker-model-2_0` | [`fapi-2_0-attacker-model`](https://openid.net/specs/fapi-2_0-attacker-model.html) | no redirect stub | redirect to fapi-attacker-model-2_0 | Merged into fapi-attacker-model-2_0 (same title in documents). Add a "Renamed Specification" stub at https://openid.net/specs/fapi-2_0-attacker-model.html. |
| JWT Secured Authorization Response Mode for OAuth 2.0 (JARM)<br>`oauth-v2-jarm` | [`openid-financial-api-jarm`](https://openid.net/specs/openid-financial-api-jarm.html) | no redirect stub | redirect to oauth-v2-jarm | Merged into oauth-v2-jarm (curated (overrides.json)). Add a "Renamed Specification" stub at https://openid.net/specs/openid-financial-api-jarm.html. |
| OpenID Continuous Access Evaluation Profile 1.0<br>`openid-caep-1_0` | [`openid-caep-specification-1_0`](https://openid.net/specs/openid-caep-specification-1_0.html) | no redirect stub | redirect to openid-caep-1_0 | Merged into openid-caep-1_0 (same title in documents). Add a "Renamed Specification" stub at https://openid.net/specs/openid-caep-specification-1_0.html. |
| OpenID Connect Client-Initiated Backchannel Authentication Flow - Core 1.0<br>`openid-client-initiated-backchannel-authentication-core-1_0` | [`openid-connect-modrna-client-initiated-backchannel-authentication-1_0`](https://openid.net/specs/openid-connect-modrna-client-initiated-backchannel-authentication-1_0.html) | no redirect stub | redirect to openid-client-initiated-backchannel-authentication-core-1_0 | Merged into openid-client-initiated-backchannel-authentication-core-1_0 (curated (overrides.json)). Add a "Renamed Specification" stub at https://openid.net/specs/openid-connect-modrna-client-initiated-backchannel-authentication-1_0.html. |
| OpenID RISC Profile Specification 1.0<br>`openid-risc-1_0` | [`openid-risc-profile-specification-1_0`](https://openid.net/specs/openid-risc-profile-specification-1_0.html) | no redirect stub | redirect to openid-risc-1_0 | Merged into openid-risc-1_0 (same title in documents). Add a "Renamed Specification" stub at https://openid.net/specs/openid-risc-profile-specification-1_0.html. |
| OpenID Shared Signals Framework Specification 1.0<br>`openid-sharedsignals-framework-1_0` | [`openid-sse-framework-1_0`](https://openid.net/specs/openid-sse-framework-1_0.html) | no redirect stub | redirect to openid-sharedsignals-framework-1_0 | Merged into openid-sharedsignals-framework-1_0 (curated (overrides.json)). Add a "Renamed Specification" stub at https://openid.net/specs/openid-sse-framework-1_0.html. |

## Working group not stated — active specs (add to source)

Latest revision is 2021 or later and has no workgroup field. Add `workgroup` to the xml2rfc front matter (or `<dd class="workgroup">`).

| Spec | Revision(s) | Document says | Should be | Notes |
|---|---|---|---|---|
| OpenID Connect Basic Client Profile 1.0<br>`openid-connect-basic-1_0` | [`openid-connect-basic-1_0-47`](https://openid.net/specs/openid-connect-basic-1_0-47.html) | (none) | AB/Connect | No workgroup in the document header, IANA Change Controller, or WG list address. Dashboard infers AB/Connect. |
| OpenID Connect Implicit Client Profile 1.0<br>`openid-connect-implicit-1_0` | [`openid-connect-implicit-1_0-30`](https://openid.net/specs/openid-connect-implicit-1_0-30.html) | (none) | AB/Connect | No workgroup in the document header, IANA Change Controller, or WG list address. Dashboard infers AB/Connect. |

## Inconsistent working group names (harmonise)

The same WG is spelled differently in the `workgroup` header field across specs (each spec's latest approved document, or its latest draft if none has been approved). (IANA "Change Controller" entries are not listed: those record the registrant.)

| WG | Spelling in document | Used by |
|---|---|---|
| AB/Connect | `OpenID Connect Working Group` | `openid-connect-native-sso-1_0-ID2`, `openid-connect-rp-metadata-choices-1_0-final`, `openid-connect-token-hash-algorithms-1_0-00`, `openid-federation-1_0-final`, `openid-federation-1_1-final`, `openid-federation-connect-1_1-final`, `openid-federation-entity-collection-1_0-01`, `openid-federation-extended-listing-1_0-ID1`, `openid-federation-wallet-1_0-05` |
| AB/Connect | `OpenID Connect` | `openid-4-verifiable-presentations-over-ble-1_0-00`, `openid-connect-enterprise-extensions-1_0-01`, `openid-connect-key-binding-1_0-ID1`, `openid-connect-self-issued-v2-1_0-ID1`, `openid-connect-userinfo-vc-1_0-00`, `openid-provider-commands-1_0-02` |
| AB/Connect | `connect` | `openid-connect-claims-aggregation-1_0-03` |
| AB/Connect | `Connect` | `openid-connect-ephemeral-subject-identifier-1_0-final` |
| Digital Credentials Protocols | `OpenID Digital Credentials Protocols` | `openid-4-verifiable-credential-issuance-1_0-final`, `openid-4-verifiable-presentations-1_0-final` |
| Digital Credentials Protocols | `Digital Credentials Protocols` | `openid4vc-high-assurance-interoperability-profile-1_0-final` |
| FAPI | `fapi` | `fapi-attacker-model-2_0-final`, `fapi-message-signing-2_0-final`, `fapi-security-profile-2_0-final` |
| FAPI | `FAPI` | `oauth-v2-grant-management-ID1`, `oauth-v2-jarm-errata1` |
| eKYC & IDA | `eKYC-IDA` | `openid-connect-4-ida-attachments-1_0-final`, `openid-connect-4-ida-claims-1_0-final`, `openid-connect-4-identity-assurance-1_0-errata1`, `openid-connect-advanced-syntax-for-claims-1_0-ID1`, `openid-ida-verified-claims-1_0-errata1` |
| eKYC & IDA | `OpenID eKYC-IDA` | `openid-ida-identity-proofing-extension-1_0-00` |
| iGov | `OpenID iGov Working Group` | `openid-igov-oauth2-1_0-ID2` |
| iGov | `OpenID Foundation iGov Working Group` | `openid-igov-use-cases-1_0-01` |

## Other metadata

Dates missing from documents and probable author-name typos.

| Spec | Revision(s) | Document says | Should be | Notes |
|---|---|---|---|---|
| OpenID Connect Artifact Binding 1.0<br>`openid-connect-ab-1_0` | [`openid-connect-ab-1_0-02`](https://openid.net/specs/openid-connect-ab-1_0-02.html) | J. Bradeley | J. Bradley | "J. Bradeley" appears 2 time(s); "J. Bradley" appears 20 times. |
| OpenID Connect Artifact Binding 1.0<br>`openid-connect-ab-1_0` | [`openid-connect-ab-1_0-02`](https://openid.net/specs/openid-connect-ab-1_0-02.html) | Breno de Madeiros | Breno de Medeiros | "Breno de Madeiros" appears 2 time(s); "Breno de Medeiros" appears 207 times. |
| OpenID Connect Authorization Code Binding 1.0<br>`openid-connect-code-1_0` | [`openid-connect-code-1_0-02`](https://openid.net/specs/openid-connect-code-1_0-02.html) | J. Bradeley | J. Bradley | "J. Bradeley" appears 2 time(s); "J. Bradley" appears 20 times. |
| OpenID Connect Authorization Code Binding 1.0<br>`openid-connect-code-1_0` | [`openid-connect-code-1_0-02`](https://openid.net/specs/openid-connect-code-1_0-02.html) | Breno de Madeiros | Breno de Medeiros | "Breno de Madeiros" appears 2 time(s); "Breno de Medeiros" appears 207 times. |

## Working group not stated — historical specs (low priority)

Last revised before 2021. Listed for completeness; fix only if the spec is republished.

| Spec | Revision(s) | Document says | Should be | Notes |
|---|---|---|---|---|
| JSON Web Encryption (JWE)<br>`draft-jones-json-web-encryption` **(overridden)** | [`draft-jones-json-web-encryption-02`](https://openid.net/specs/draft-jones-json-web-encryption-02.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| JSON Web Key (JWK)<br>`draft-jones-json-web-key` **(overridden)** | [`draft-jones-json-web-key-03`](https://openid.net/specs/draft-jones-json-web-key-03.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| JSON Web Signature (JWS)<br>`draft-jones-json-web-signature` **(overridden)** | [`draft-jones-json-web-signature-04`](https://openid.net/specs/draft-jones-json-web-signature-04.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| JSON Web Token (JWT)<br>`draft-jones-json-web-token` **(overridden)** | [`draft-jones-json-web-token-07`](https://openid.net/specs/draft-jones-json-web-token-07.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| JSON Web Token (JWT) Bearer Token Profiles for OAuth 2.0<br>`draft-jones-oauth-jwt-bearer` **(overridden)** | [`draft-jones-oauth-jwt-bearer-03`](https://openid.net/specs/draft-jones-oauth-jwt-bearer-03.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| Simple Web Discovery (SWD)<br>`draft-jones-simple-web-discovery` **(overridden)** | [`draft-jones-simple-web-discovery-02`](https://openid.net/specs/draft-jones-simple-web-discovery-02.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| FastFed 1.0<br>`fastfed-1_0` | [`fastfed-1_0-00`](https://openid.net/specs/fastfed-1_0-00.html) | (none) | FastFed | No workgroup in the document header, IANA Change Controller, or WG list address. Dashboard infers FastFed. |
| FastFed Core 1.0<br>`fastfed-core-1_0` | [`fastfed-core-1_0-ID1`](https://openid.net/specs/fastfed-core-1_0-ID1.html) | (none) | FastFed | No workgroup in the document header, IANA Change Controller, or WG list address. Dashboard infers FastFed. |
| FastFed Enterprise SAML Profile 1.0<br>`fastfed-saml-1_0` | [`fastfed-saml-1_0-ID1`](https://openid.net/specs/fastfed-saml-1_0-ID1.html) | (none) | FastFed | No workgroup in the document header, IANA Change Controller, or WG list address. Dashboard infers FastFed. |
| FastFed Enterprise SCIM Profile 1.0<br>`fastfed-scim-1_0` | [`fastfed-scim-1_0-ID1`](https://openid.net/specs/fastfed-scim-1_0-ID1.html) | (none) | FastFed | No workgroup in the document header, IANA Change Controller, or WG list address. Dashboard infers FastFed. |
| Identity Attribute Metadata<br>`identity-attribute-metadata-1_0` | [`identity-attribute-metadata-1_0-01`](https://openid.net/specs/identity-attribute-metadata-1_0-01.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| OAuth Event Types 1.0<br>`oauth-event-types-1_0` | [`oauth-event-types-1_0-ID1`](https://openid.net/specs/oauth-event-types-1_0-ID1.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| OAuth 2.0 Form Post Response Mode<br>`oauth-v2-form-post-response-mode-1_0` | [`oauth-v2-form-post-response-mode-1_0-final`](https://openid.net/specs/oauth-v2-form-post-response-mode-1_0-final.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| OpenID Assertion Quality Extension 1.0<br>`openid-assertion-quality-extension-1_0` | [`openid-assertion-quality-extension-1_0-03`](https://openid.net/specs/openid-assertion-quality-extension-1_0-03.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| OpenID Attribute Exchange 1.0<br>`openid-attribute-exchange-1_0` | [`openid-attribute-exchange-1_0`](https://openid.net/specs/openid-attribute-exchange-1_0.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| Attribute Properties for OpenID Attribute Exchange<br>`openid-attribute-properties-list-1_0` | [`openid-attribute-properties-list-1_0-01`](https://openid.net/specs/openid-attribute-properties-list-1_0-01.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| OpenID Attribute Types<br>`openid-attribute-types-1_0` | [`openid-attribute-types-1_0-02`](https://openid.net/specs/openid-attribute-types-1_0-02.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| OpenID Authentication 1.1<br>`openid-authentication-1_1` | [`openid-authentication-1_1`](https://openid.net/specs/openid-authentication-1_1.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| OpenID Authentication 2.0<br>`openid-authentication-2_0` | [`openid-authentication-2_0`](https://openid.net/specs/openid-authentication-2_0.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| OpenID Authentication 2.0 - Pre<br>`openid-authentication-2_0-pre11` | [`openid-authentication-2_0-pre11`](https://openid.net/specs/openid-authentication-2_0-pre11.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| OpenID Authentication Security Profiles<br>`openid-authentication-security-profiles` | [`openid-authentication-security-profiles-01`](https://openid.net/specs/openid-authentication-security-profiles-01.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| OpenID Connect Account Porting<br>`openid-connect-account-porting-1_0` | [`openid-connect-account-porting-1_0-ID1`](https://openid.net/specs/openid-connect-account-porting-1_0-ID1.html) | (none) | AB/Connect | No workgroup in the document header, IANA Change Controller, or WG list address. Dashboard infers AB/Connect. |
| OpenID 2.0 to OpenID Connect Migration 1.0<br>`openid-connect-migration-1_0` | [`openid-connect-migration-1_0-final`](https://openid.net/specs/openid-connect-migration-1_0-final.html) | (none) | AB/Connect | No workgroup in the document header, IANA Change Controller, or WG list address. Dashboard infers AB/Connect. |
| OpenID Connect MODRNA Authentication Profile 1.0<br>`openid-connect-modrna-authentication-1_0` | [`openid-connect-modrna-authentication-1_0-ID1`](https://openid.net/specs/openid-connect-modrna-authentication-1_0-ID1.html) | (none) | MODRNA | No workgroup in the document header, IANA Change Controller, or WG list address. Dashboard infers MODRNA. |
| MODRNA: Client Initiated Backchannel Authentication Profile 1.0<br>`openid-connect-modrna-client-initiated-backchannel-authentication-profile-1_0` | [`openid-connect-modrna-client-initiated-backchannel-authentication-profile-1_0-03`](https://openid.net/specs/openid-connect-modrna-client-initiated-backchannel-authentication-profile-1_0-03.html) | (none) | MODRNA | No workgroup in the document header, IANA Change Controller, or WG list address. Dashboard infers MODRNA. |
| OpenID Connect MODRNA Discovery Profile 1.0<br>`openid-connect-modrna-discovery-1_0` | [`openid-connect-modrna-discovery-1_0-05`](https://openid.net/specs/openid-connect-modrna-discovery-1_0-05.html) | (none) | MODRNA | No workgroup in the document header, IANA Change Controller, or WG list address. Dashboard infers MODRNA. |
| OpenID Connect User Questioning API 1.0<br>`openid-connect-user-questioning-api-1_0` **(overridden)** | [`openid-connect-user-questioning-api-1_0-ID2`](https://openid.net/specs/openid-connect-user-questioning-api-1_0-ID2.html) | (none) | MODRNA | No workgroup in the document header, IANA Change Controller, or WG list address. Dashboard shows MODRNA, set in overrides.json. |
| OpenID DTP Version 1.0 Adjuncts<br>`openid-dtp-adjuncts-1_0` | [`openid-dtp-adjuncts-1_0-02`](https://openid.net/specs/openid-dtp-adjuncts-1_0-02.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| OpenID DTP Version 1.0 Envelopes<br>`openid-dtp-envelopes-1_0` | [`openid-dtp-envelopes-1_0-02`](https://openid.net/specs/openid-dtp-envelopes-1_0-02.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| OpenID DTP Messages 1.0<br>`openid-dtp-messages-1_0` | [`openid-dtp-messages-1_0-03`](https://openid.net/specs/openid-dtp-messages-1_0-03.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| Financial-grade API: Client Initiated Backchannel Authentication Profile<br>`openid-financial-api-ciba` | [`openid-financial-api-ciba-ID1`](https://openid.net/specs/openid-financial-api-ciba-ID1.html) | (none) | FAPI | No workgroup in the document header, IANA Change Controller, or WG list address. Dashboard infers FAPI. |
| Health Relationship Trust Profile for Fast Healthcare Interoperability Resources (FHIR) UMA Resources<br>`openid-heart-fhir-uma-1_0` | [`openid-heart-fhir-uma-1_0-ID1`](https://openid.net/specs/openid-heart-fhir-uma-1_0-ID1.html) | (none) | HEART | No workgroup in the document header, IANA Change Controller, or WG list address. Dashboard infers HEART. |
| Health Relationship Trust Profile for Fast Healthcare Interoperability Resources (FHIR) UMA 2 Resources<br>`openid-heart-fhir-uma2-1_0` | [`openid-heart-fhir-uma2-1_0-ID1`](https://openid.net/specs/openid-heart-fhir-uma2-1_0-ID1.html) | (none) | HEART | No workgroup in the document header, IANA Change Controller, or WG list address. Dashboard infers HEART. |
| Health Relationship Trust Profile for OAuth 2.0<br>`openid-heart-oauth2-1_0` | [`openid-heart-oauth2-1_0-ID3`](https://openid.net/specs/openid-heart-oauth2-1_0-ID3.html) | (none) | HEART | No workgroup in the document header, IANA Change Controller, or WG list address. Dashboard infers HEART. |
| Health Relationship Trust Profile for OpenID Connect 1.0<br>`openid-heart-openid-connect-1_0` | [`openid-heart-openid-connect-1_0-ID2`](https://openid.net/specs/openid-heart-openid-connect-1_0-ID2.html) | (none) | HEART | No workgroup in the document header, IANA Change Controller, or WG list address. Dashboard infers HEART. |
| Health Relationship Trust Profile for User-Managed Access 1.0<br>`openid-heart-uma-1_0` | [`openid-heart-uma-1_0-ID2`](https://openid.net/specs/openid-heart-uma-1_0-ID2.html) | (none) | HEART | No workgroup in the document header, IANA Change Controller, or WG list address. Dashboard infers HEART. |
| Health Relationship Trust Profile for User-Managed Access 2.0<br>`openid-heart-uma2-1_0` | [`openid-heart-uma2-1_0-ID1`](https://openid.net/specs/openid-heart-uma2-1_0-ID1.html) | (none) | HEART | No workgroup in the document header, IANA Change Controller, or WG list address. Dashboard infers HEART. |
| OpenID Provider Authentication Policy Extension 1.0<br>`openid-provider-authentication-policy-extension-1_0` | [`openid-provider-authentication-policy-extension-1_0`](https://openid.net/specs/openid-provider-authentication-policy-extension-1_0.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| OpenID RISC Event Types 1.0<br>`openid-risc-event-types-1_0` | [`openid-risc-event-types-1_0-ID1`](https://openid.net/specs/openid-risc-event-types-1_0-ID1.html) | (none) | Shared Signals | No workgroup in the document header, IANA Change Controller, or WG list address. Dashboard infers Shared Signals. |
| OpenID Service Key Discovery 1.0<br>`openid-service-key-discovery-1_0` | [`openid-service-key-discovery-1_0-01`](https://openid.net/specs/openid-service-key-discovery-1_0-01.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| OpenID Simple Registration Extension 1.0<br>`openid-simple-registration-extension-1_0` | [`openid-simple-registration-extension-1_0`](https://openid.net/specs/openid-simple-registration-extension-1_0.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| OpenID Simple Registration Extension 1.1<br>`openid-simple-registration-extension-1_1` | [`openid-simple-registration-extension-1_1-01`](https://openid.net/specs/openid-simple-registration-extension-1_1-01.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| OpenYOLO for Android<br>`openyolo-android` | [`openyolo-android-ID1`](https://openid.net/specs/openyolo-android-ID1.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
| Yadis Specification Version 1.0<br>`yadis-v1.0` | [`yadis-v1.0`](https://openid.net/specs/yadis-v1.0.html) | (none) | ? | No workgroup in the document header, IANA Change Controller, or WG list address. |
