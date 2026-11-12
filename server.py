# Eclipse Covenant MCP
# Copyright © 2026 Cyan Eclipse Technologies LLC · cetech.ai
# Stdio MCP server: disjoint agent (14 tools) / operator surfaces.

"""Eclipse Covenant MCP — v0.1.0, P0 (consent-bound lead work).

Powered by Cyan Eclipse Technologies (cetech.ai).

Descriptor: Eclipse Covenant — consent-bound lead work for
real-estate agents: every lead carries its provenance, every outreach
is checked at send time, and every session seals into the brokerage's
defense file. It does not sell leads, hold MLS data, or perform
licensed acts.

P0 SCOPE: SYNTHETIC ONLY. Simulator send routes record, never
transmit. No live outreach, no real leads, no live API keys, no real
CRM/DNC access. Counsel HARD GATE stands before any P1 live outreach.

SURFACES (disjoint, spec 5.4): $ECLIPSE_COVENANT_SURFACE selects
"agent" (default; exactly the 14 enumerated tools) or "operator"
(mandate_create / pack_retrieve / consent_record_verify only — no
operator tool touches a single send).

Transport: MCP over stdio (newline-delimited JSON-RPC 2.0), stdlib
only. State: $ECLIPSE_COVENANT_STATE or ./data/state.json.
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import covenant_engine as eng  # noqa: E402
import signing  # noqa: E402
from covenant_engine import ToolError  # noqa: E402

STATE_PATH = Path(os.environ.get(
    "ECLIPSE_COVENANT_STATE", HERE / "data" / "state.json"))
SURFACE = os.environ.get("ECLIPSE_COVENANT_SURFACE", "agent")

AGENT_TOOLS = list(eng.TOOLS.keys())
OPERATOR_TOOLS = ["mandate_create", "pack_retrieve",
                  "consent_record_verify"]


def load_state():
    if STATE_PATH.exists():
        saved = json.loads(STATE_PATH.read_text())
        fresh = eng.empty_state()
        fresh.update(saved)
        fresh["_config"] = eng.empty_state()["_config"]
        return fresh
    return eng.empty_state()


def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=1))


def pack_retrieve(state, args):
    """Operator-only: pack retrieval for the broker of record."""
    pack_id = eng.require_ref(args.get("pack_id"), "pack_id")
    pack = state["packs"].get(pack_id)
    if pack is None:
        raise ToolError("PACK_NOT_FOUND", f"no pack {pack_id}")
    return pack


def _ann(read_only, destructive=False, idempotent=False):
    return {"readOnlyHint": read_only,
            "destructiveHint": destructive,
            "idempotentHint": idempotent,
            "openWorldHint": False}


def _sp(desc, **kw):
    prop = {"type": "string", "description": desc}
    prop.update(kw)
    return prop


def _op(desc, **kw):
    prop = {"type": "object", "description": desc}
    prop.update(kw)
    return prop


def _ap(desc, items=None, **kw):
    prop = {"type": "array", "description": desc}
    if items is not None:
        prop["items"] = items
    prop.update(kw)
    return prop


def _bp(desc):
    return {"type": "boolean", "description": desc}


def _ip(desc):
    return {"type": "integer", "description": desc}


def _out(props, required=None):
    schema = {"type": "object", "properties": props}
    if required:
        schema["required"] = required
    return schema


# name -> (description, input properties, required, annotations,
#          outputSchema)
TOOL_DEFS = {}

_CTXT = ("Local stdio server running synthetic data only: no network, "
         "no real leads, no live CRM or do-not-call registry access, "
         "no authentication and no rate limit; state persists to the "
         "server state JSON file after each call.")


TOOL_DEFS["lead_intake"] = (
    "Intake a lead under a brokerage mandate and mint (or refresh) "
    "its consent record with a graded provenance class. Use when a "
    "lead first arrives or is re-submitted; use "
    "consent_attach_certificate instead to add certificate evidence "
    "to an existing record, and consent_record_read to read a record "
    "back. Mutating and persistent: creates the lead and a sealed, "
    "hash-chained record, or — for a duplicate identity key under "
    "the same mandate — merges onto the existing record (class "
    "never downgrades, revocations and evidence are preserved, "
    "version increments). Provenance is graded from evidence only: "
    "CERTIFIED_CAPTURE when the supplied certificate verifies "
    "against the fixture registry and binds to this lead, "
    "SELF_CAPTURED when verbatim disclosure text plus a form "
    "snapshot are stored, VENDOR_ASSERTED for portal/vendor/CRM "
    "sources, otherwise LEGACY_UNVERIFIED, which permits no "
    "automated outreach. A free-text consent_note is recorded as "
    "data, never as evidence. Argument keys that would effect an "
    "export, transfer, or gate bypass are refused by name at any "
    "nesting depth. Fails with MANDATE_NOT_FOUND for an unknown "
    "mandate and RULE_PACK_UNAVAILABLE when the rule pack cannot "
    "load. " + _CTXT + " Returns {lead_id, record_id, "
    "provenance_class, evidence_gaps, rule_version}.",
    {"mandate_id": _sp("Mandate id ('MND-####') created on the "
                       "operator surface; the record is bound to "
                       "this mandate only."),
     "identity": _op("Lead identity as given. 'phones' and "
                     "'emails' must be lists when present; the "
                     "first phone's digits (else the first email, "
                     "lowercased) form the identity key used for "
                     "duplicate detection."),
     "source": _op("Acquisition source object: 'kind' one of "
                   "MANUAL, PORTAL_PROGRAM, VENDOR_FEED, CRM_IMPORT; "
                   "plus vendor_name, program_name, distribution, "
                   "and program_channel where applicable."),
     "capture": _op("Capture evidence object: surface, "
                    "occurred_at, disclosure_text_verbatim, "
                    "disclosure_version, form_snapshot_ref. Verbatim "
                    "disclosure text plus a form snapshot together "
                    "support the SELF_CAPTURED class."),
     "certificate_ref": _sp("Certificate reference to verify in "
                            "the fixture certificate registry at "
                            "intake; must bind to this lead's "
                            "identity key to verify."),
     "certificate_issuer": _sp("Issuer label recorded with the "
                               "certificate evidence; defaults to "
                               "TRUSTEDFORM."),
     "channel_grants": _op("Per-channel consent grants keyed by "
                           "channel (voice, text, email); each grant "
                           "is an object with granted_at, basis "
                           "(PEWC, EXPRESS, or "
                           "EXISTING_RELATIONSHIP_PER_PARAMS), and "
                           "scope_note. Grants are per-channel: a "
                           "voice grant never covers text."),
     "named_seller_set": _ap("Brokerage/agent names covered by "
                             "the disclosure, as a list of strings. "
                             "Only a sending identity in this set "
                             "can pass the send gate for this lead.",
                             items={"type": "string"}),
     "consent_note": _sp("Free-text caller note about consent. "
                         "Recorded as data only; it never raises "
                         "the provenance class."),
     "crm_ref": _sp("Caller's CRM reference for the lead, stored "
                    "as supplied."),
     "at_time": _sp("ISO 8601 event time; defaults to the server "
                    "clock when omitted.")},
    ["mandate_id", "named_seller_set"], _ann(False),
    _out({"lead_id": _sp("Assigned lead id, e.g. 'LEAD-0001'."),
          "record_id": _sp("Consent record id, e.g. 'REC-0001'."),
          "provenance_class": _sp("One of CERTIFIED_CAPTURE, "
                                  "SELF_CAPTURED, VENDOR_ASSERTED, "
                                  "LEGACY_UNVERIFIED."),
          "evidence_gaps": _ap("Named evidence gaps on the record.",
                               items={"type": "string"}),
          "rule_version": _op("Rule pack reference in force: "
                              "{set_id, version, hash, set_by}.")},
         ["lead_id", "record_id", "provenance_class"]))

TOOL_DEFS["consent_attach_certificate"] = (
    "Attach a consent certificate to an existing consent record "
    "and re-grade its provenance class from the verification "
    "result. Use after lead_intake when certificate evidence "
    "arrives late; use lead_intake instead for a new lead, and "
    "consent_record_read to inspect the updated record. Mutating "
    "and persistent: appends the certificate evidence, increments "
    "the record version, and re-seals the record's hash chain. A "
    "verifying certificate (PASS, bound to this lead) raises the "
    "class to CERTIFIED_CAPTURE; a failed or unverifiable "
    "certificate leaves the honest remainder class computed from "
    "the remaining evidence and adds a named evidence gap — "
    "certificates are evidence, never authorization by themselves. "
    "Not idempotent: each call appends another evidence entry. "
    "Fails with RECORD_NOT_FOUND for an unknown record_id. " +
    _CTXT + " Returns {record_id, verify_status, detail, "
    "provenance_class}.",
    {"record_id": _sp("Consent record id returned by lead_intake."),
     "trustedform_cert_url": _sp("TrustedForm certificate "
                                 "reference/URL to verify; when "
                                 "supplied it takes precedence over "
                                 "leadid_token and the issuer is "
                                 "recorded as TRUSTEDFORM."),
     "leadid_token": _sp("Jornaya LeadiD token to verify; used "
                         "only when trustedform_cert_url is "
                         "absent, with issuer recorded as JORNAYA. "
                         "Supply exactly one of the two."),
     "at_time": _sp("ISO 8601 verification time; defaults to the "
                    "server clock.")},
    ["record_id"], _ann(False),
    _out({"record_id": _sp("The record updated."),
          "verify_status": _sp("PASS, FAIL, or "
                               "UNVERIFIABLE_OFFLINE."),
          "detail": _sp("Verifier's explanation of the result."),
          "provenance_class": _sp("Record class after re-grading.")},
         ["record_id", "verify_status", "provenance_class"]))

TOOL_DEFS["consent_record_read"] = (
    "Read one full consent record by record_id, exactly as "
    "sealed: identity, provenance class, capture and certificate "
    "evidence, channel grants, named sellers, revocation state "
    "and history, evidence gaps, and the hash-chain fields. Use "
    "for a single known record; use consent_history instead for "
    "the lead's event timeline, and consent_record_verify to "
    "independently check a record's integrity. Read-only: the "
    "record is never altered by a read, but reads are counted by "
    "an export detector — a bulk flag (bulk or all_records set "
    "true, including the strings 'true'/'yes'/'1') is refused "
    "with LEAD_EXPORT_REFUSED because bulk reads effect an "
    "export, and more than 20 record reads inside 60 seconds is "
    "refused the same way and logged for the operator. Fails with "
    "RECORD_NOT_FOUND for an unknown id. " + _CTXT + " Returns "
    "the full record object.",
    {"record_id": _sp("Consent record id returned by lead_intake."),
     "bulk": _bp("Must be absent or false. True (or a true-like "
                 "string) is refused as an export shape."),
     "all_records": _bp("Must be absent or false. True (or a "
                        "true-like string) is refused as an "
                        "export shape.")},
    ["record_id"], _ann(True, idempotent=True),
    _out({"record_id": _sp("Record id."),
          "lead_id": _sp("Lead the record belongs to."),
          "mandate_id": _sp("Mandate the record is bound to."),
          "version": _ip("Record version; increments on every "
                         "sealed change."),
          "provenance_class": _sp("CERTIFIED_CAPTURE, "
                                  "SELF_CAPTURED, VENDOR_ASSERTED, "
                                  "or LEGACY_UNVERIFIED."),
          "channel_grants": _op("Per-channel consent grants."),
          "named_seller_set": _ap("Covered sellers.",
                                  items={"type": "string"}),
          "revocation_state": _sp("NONE, REVOKED_CHANNEL, "
                                  "REVOKED_ALL, or "
                                  "SCOPE_UNRESOLVED."),
          "revocations": _ap("Revocation entries on the record.",
                             items={"type": "object"}),
          "certificate_evidence": _ap("Certificate evidence "
                                      "entries.",
                                      items={"type": "object"}),
          "evidence_gaps": _ap("Named evidence gaps.",
                               items={"type": "string"}),
          "hash": _sp("Record content hash in the seal chain."),
          "herald_sig": _sp("Seal signature over the record hash.")},
         ["record_id", "lead_id", "provenance_class"]))

TOOL_DEFS["consent_history"] = (
    "Read the chronological event history for one lead: intake, "
    "class re-evaluations, revocations, sends, and refusals as "
    "logged. Use to reconstruct what happened to a lead over "
    "time; use consent_record_read instead for the record's "
    "current state. Read-only and unpaginated: returns every "
    "logged event for the lead. Fails with LEAD_NOT_FOUND for an "
    "unknown lead_id. " + _CTXT + " Returns {lead_id, events}, "
    "where each event carries its kind, time, actor, and detail.",
    {"lead_id": _sp("Lead id returned by lead_intake.")},
    ["lead_id"], _ann(True, idempotent=True),
    _out({"lead_id": _sp("The lead requested."),
          "events": _ap("Chronological event entries for the lead.",
                        items={"type": "object"})},
         ["lead_id", "events"]))

TOOL_DEFS["revocation_record"] = (
    "Record a lead's revocation (opt-out) verbatim and apply its "
    "blocking scope immediately. Use the moment a revocation "
    "arrives on any channel; there is no un-revoke tool — "
    "revocation history is never deleted, including by a later "
    "duplicate lead_intake. Mutating and persistent: appends the "
    "revocation to the record, re-seals it, and seals a "
    "REVOCATION entry into the lead's evidence pack. Scope is "
    "normalized from the verbatim payload against the rule pack: "
    "an all-channel phrase gives ALL_CHANNELS, a channel phrase "
    "gives CHANNEL for that channel, and a payload matching no "
    "known phrase gives UNRESOLVED, which blocks ALL channels "
    "until resolved — ambiguity never reads as 'not a "
    "revocation'. The block is effective immediately in this "
    "surface; the returned honor_deadline (received time plus "
    "the rule pack's business-day window) is the legal ceiling, "
    "not a grace period. Setting send_clarification=true fires "
    "the single permitted template-pinned clarification through "
    "the simulator route; caller-authored clarification text is "
    "refused. Fails with LEAD_NOT_FOUND, CONSENT_RECORD_MISSING, "
    "or INVALID_CHANNEL as applicable. " + _CTXT + " Returns "
    "{revocation_id, clarification_sent, normalized_scope, "
    "scope_channel, honor_deadline, blocked_effective, note}.",
    {"lead_id": _sp("Lead id the revocation binds to."),
     "raw_payload": _sp("The revocation message verbatim, exactly "
                        "as received; required and stored "
                        "unmodified. Scope is normalized from this "
                        "text."),
     "received_via_channel": _sp("Channel the revocation arrived "
                                 "on: voice, text, or email."),
     "send_clarification": _bp("When true, fire the one permitted "
                               "template-pinned clarification "
                               "(simulator-recorded). Defaults to "
                               "no clarification."),
     "clarification_body": _sp("Do not supply: clarification "
                               "text is template-pinned, and a "
                               "caller-authored body is refused "
                               "with CLARIFICATION_TEMPLATE_ONLY "
                               "when a clarification is sent."),
     "at_time": _sp("ISO 8601 receipt time; defaults to the "
                    "server clock.")},
    ["lead_id", "raw_payload", "received_via_channel"],
    _ann(False),
    _out({"revocation_id": _sp("Assigned revocation id, e.g. "
                               "'REV-0001'."),
          "clarification_sent": {"type": ["object", "null"],
                                 "description": "The clarification "
                                 "record, or null when none was "
                                 "sent."},
          "normalized_scope": _sp("ALL_CHANNELS, CHANNEL, or "
                                  "UNRESOLVED."),
          "scope_channel": _sp("Channel blocked for CHANNEL "
                               "scope; otherwise null."),
          "honor_deadline": _sp("ISO 8601 legal honor deadline."),
          "blocked_effective": _sp("ISO 8601 time the in-surface "
                                   "block took effect.")},
         ["revocation_id", "normalized_scope", "honor_deadline"]))

TOOL_DEFS["lead_context_read"] = (
    "Read the synthetic fixture context stored for a lead "
    "(enrichment data for preparation, not outreach). Use to "
    "prepare for contact; use consent_record_read for the "
    "consent record itself. Read-only and consent-independent: "
    "it works for leads with no consent record, creates no "
    "record, and grants no outreach authority — enrichment is "
    "not authorization. The context is fixture data labeled "
    "synthetic; it is never live CRM data. Fails with "
    "LEAD_NOT_FOUND for an unknown lead or CONTEXT_UNAVAILABLE "
    "when the fixture context cannot be read. " + _CTXT +
    " Returns {lead_id, synthetic, label, context, note}.",
    {"lead_id": _sp("Lead id returned by lead_intake.")},
    ["lead_id"], _ann(True, idempotent=True),
    _out({"lead_id": _sp("The lead requested."),
          "synthetic": _bp("Always true: fixture data only."),
          "label": _sp("Synthetic-data label carried on the "
                       "payload."),
          "context": _op("Fixture context object for the lead."),
          "note": _sp("Reminder that context confers no outreach "
                      "authority.")},
         ["lead_id", "synthetic", "context"]))


def _send_props(extra):
    props = {
        "lead_id": _sp("Lead id to contact; the consent record "
                       "must exist under mandate_id."),
        "mandate_id": _sp("Mandate id presented for this send; "
                          "sending_identity must be a seat on it."),
        "sending_identity": _sp("Sending agent/brokerage identity. "
                                "Must be a seat on the mandate AND "
                                "in the record's named-seller set; "
                                "identity is taken from the mandate, "
                                "never from a caller claim alone."),
        "audience_criteria": _sp("Optional targeting criteria "
                                 "string; it is screened by "
                                 "criteria_screen as part of the "
                                 "gate and protected or proxy "
                                 "criteria refuse the send."),
        "at_time": _sp("ISO 8601 send time; defaults to the "
                       "server clock. Rule-pack staleness and the "
                       "do-not-call scrub are evaluated at this "
                       "time.")}
    props.update(extra)
    return props


_SEND_OUT = _out(
    {"send_id": _sp("Assigned send id, e.g. 'SEND-0001'."),
     "status": _sp("Always SENT_SIMULATOR on success: recorded, "
                   "never transmitted."),
     "route": _sp("Simulator route label."),
     "channel": _sp("voice, text, or email."),
     "lead_id": _sp("Lead contacted."),
     "provenance_class": _sp("Provenance class the gate "
                             "evaluated."),
     "at": _sp("ISO 8601 send time."),
     "check_transcript": _op("Six-step gate transcript with a "
                             "PASS or named refusal per step, plus "
                             "scrub and guard findings.")},
    ["send_id", "status", "channel", "lead_id"])

_GATE_BEHAVIOUR = (
    "Every send runs the same six-step gate at send time, in "
    "order: consent record exists under this mandate (a "
    "LEGACY_UNVERIFIED record always refuses) -> a per-channel "
    "grant covers this channel -> the sender is in the named-"
    "seller set -> no open revocation blocks the channel (an "
    "unresolved-scope revocation blocks all channels) -> a fresh "
    "do-not-call scrub loaded from disk at this send (voice/text "
    "only; a listed number refuses unless the grant basis is "
    "PEWC) -> copy and criteria screens over the payload. The "
    "first failure stops the pipeline, later steps are recorded "
    "NOT_RUN_UPSTREAM_REFUSAL, and both sends and refusals are "
    "sealed into the lead's evidence pack. Vendor-asserted leads "
    "additionally obey the mandate's vendor posture "
    "(NARROW_FIRST_CONTACT_ONLY allows one first contact on the "
    "program channel; REFUSE_ALL refuses). Mutating and "
    "persistent, not idempotent: each call is a new send with a "
    "new send_id. SIMULATOR ONLY: a successful call records the "
    "send and never transmits anything. ")

TOOL_DEFS["outreach_text"] = (
    "Send a text message to a lead through the consent gate — "
    "the only text-send path in this server. Use for SMS-style "
    "outreach to an intaken lead; use outreach_email for email, "
    "outreach_call_place for voice, copy_screen to pre-check "
    "wording without sending, and followup_sequence_plan for a "
    "multi-step sequence. " + _GATE_BEHAVIOUR + _CTXT +
    " Returns the send receipt {send_id, status, route, channel, "
    "lead_id, provenance_class, at, check_transcript}; refusals "
    "return a named refusal class instead.",
    _send_props({"body": _sp("Message text, screened verbatim by "
                             "the copy screen; any screen finding "
                             "blocks the send.")}),
    ["lead_id", "mandate_id", "sending_identity", "body"],
    _ann(False), _SEND_OUT)

TOOL_DEFS["outreach_call_place"] = (
    "Place a voice call to a lead through the consent gate — "
    "the only voice-send path in this server. Use for call "
    "outreach to an intaken lead; use outreach_text for text and "
    "outreach_email for email. " + _GATE_BEHAVIOUR +
    "DIALER STUB: no call is actually placed — the route is a "
    "simulator dialer that records the attempt (a live voice "
    "provider is not connected in this build). The "
    "call_purpose_class string is what the gate screens as the "
    "call's payload. " + _CTXT + " Returns the send receipt "
    "{send_id, status, route, channel, lead_id, "
    "provenance_class, at, check_transcript} with the stub route "
    "named; refusals return a named refusal class instead.",
    _send_props({"call_purpose_class": _sp(
        "Purpose class label for the call, screened by the gate "
        "in place of a message body, e.g. an appointment-confirm "
        "or follow-up class label.")}),
    ["lead_id", "mandate_id", "sending_identity",
     "call_purpose_class"], _ann(False), _SEND_OUT)

TOOL_DEFS["outreach_email"] = (
    "Send an email to a lead through the consent gate — the "
    "only email-send path in this server. Use for email outreach "
    "to an intaken lead; use outreach_text for text and "
    "outreach_call_place for voice. " + _GATE_BEHAVIOUR +
    "For email the do-not-call scrub step is recorded "
    "NOT_APPLICABLE_CHANNEL (email is not a registry channel); "
    "the screened payload is the subject line plus body "
    "combined. SIMULATOR ONLY: recorded, never transmitted. " +
    _CTXT + " Returns the send receipt {send_id, status, route, "
    "channel, lead_id, provenance_class, at, check_transcript}; "
    "refusals return a named refusal class instead.",
    _send_props({"subject": _sp("Email subject line; screened "
                                "together with the body."),
                 "body": _sp("Email body text; screened together "
                             "with the subject.")}),
    ["lead_id", "mandate_id", "sending_identity"],
    _ann(False), _SEND_OUT)

TOOL_DEFS["followup_sequence_plan"] = (
    "Create, approve, or run one step of a follow-up outreach "
    "sequence for a lead, selected by the mode parameter. Use "
    "instead of repeated single outreach calls when contact is "
    "a planned sequence; use outreach_text, outreach_call_place, "
    "or outreach_email for a one-off send. Mutating and "
    "persistent in every mode. mode=create stores a plan of at "
    "most 50 steps in PENDING_APPROVAL with every step rendered "
    "as DRAFT — oversized plans are refused as a de-facto blast. "
    "mode=approve records a human approval only when approval_sig "
    "verifies as a signature over plan_id plus approver; approval "
    "is never send authorization. mode=run_step sends exactly one "
    "approved step through the full send gate at its own send "
    "time (a body that differs from the approved step re-opens "
    "the plan and refuses); on a gate refusal the plan halts "
    "unless on_refusal=CONTINUE. " + _CTXT + " Returns per mode: "
    "create {plan_id, state, steps_rendered_as}; approve "
    "{plan_id, state, note}; run_step {plan_id, step_index, "
    "step_state, receipt}.",
    {"mode": _sp("create (default), approve, or run_step."),
     "lead_id": _sp("create: lead the sequence targets; must "
                    "already exist."),
     "mandate_id": _sp("create: mandate stored on the plan and "
                       "presented again at each step's send gate."),
     "steps": _ap("create: ordered steps, 1 to 50, each an object "
                  "with channel (voice, text, or email), body, "
                  "and offset_hours.",
                  items={"type": "object"}),
     "on_refusal": _sp("create: HALT (default) or CONTINUE — "
                       "whether a gate refusal on one step halts "
                       "the whole plan."),
     "plan_id": _sp("approve/run_step: plan id returned by "
                    "create."),
     "approver": _sp("approve: human approver identity the "
                     "signature binds."),
     "approval_sig": _sp("approve: signature over plan_id plus "
                         "approver; unverified approvals are "
                         "refused with APPROVAL_UNVERIFIED."),
     "step_index": _ip("run_step: zero-based index of the step "
                       "to send; digit strings are coerced."),
     "sending_identity": _sp("run_step: sending identity "
                             "presented to that step's send "
                             "gate."),
     "body": _sp("run_step: optional; when supplied it must "
                 "equal the approved step body exactly, or the "
                 "plan re-opens and the step refuses as "
                 "unapproved."),
     "at_time": _sp("ISO 8601 time for the operation; defaults "
                    "to the server clock.")},
    [], _ann(False),
    _out({"plan_id": _sp("Plan id, e.g. 'PLAN-0001'."),
          "state": _sp("PENDING_APPROVAL, APPROVED, or HALTED."),
          "steps_rendered_as": _sp("create only: DRAFT."),
          "step_index": _ip("run_step only: the step sent."),
          "step_state": _sp("run_step only: SENT."),
          "receipt": _op("run_step only: the step's send "
                         "receipt.")},
         ["plan_id"]))

TOOL_DEFS["showing_schedule"] = (
    "Schedule a property showing for a lead as a clerical "
    "logistics record. Use for appointment logistics only; use "
    "the outreach tools to send any message about the showing — "
    "scheduling itself sends nothing and is not outreach "
    "consent. The logistics payload is scanned for licensed-act "
    "content (negotiation, counteroffer, opinion of value, "
    "appraisal, contract terms, price or legal advice) and any "
    "hit refuses with LICENSED_ACT_REFUSED: those acts route to "
    "the licensee, never this tool. This call records no "
    "persistent booking in this build — it validates and "
    "returns the scheduling status; treat the return as the "
    "record. Fails with LEAD_NOT_FOUND for an unknown lead. " +
    _CTXT + " Returns {lead_id, status: SCHEDULED_CLERICAL, "
    "window, note}.",
    {"lead_id": _sp("Lead id the showing is for."),
     "window": _sp("Showing window as a string, e.g. 'Sat "
                   "10:00'; returned verbatim."),
     "logistics": _op("Logistics details object (address, "
                      "access, timing). Scanned for licensed-act "
                      "content; negotiation or price content "
                      "refuses the call.")},
    ["lead_id"], _ann(False),
    _out({"lead_id": _sp("Lead scheduled for."),
          "status": _sp("SCHEDULED_CLERICAL."),
          "window": _sp("Window as supplied."),
          "note": _sp("Reminder that scheduling is not outreach "
                      "consent.")},
         ["lead_id", "status"]))

TOOL_DEFS["copy_screen"] = (
    "Screen message copy against the closed, versioned "
    "fair-housing copy vocabulary and return findings with "
    "character spans. Use to pre-check outreach wording without "
    "sending; the send gate also runs this screen itself, so a "
    "clean pre-check does not guarantee a send. Read-only: the "
    "text is returned byte-for-byte unmodified with its content "
    "hash — this tool never rewrites copy. Fails closed with "
    "VOCABULARY_UNAVAILABLE when the vocabulary pack cannot be "
    "loaded. " + _CTXT + " Returns {text, text_unmodified, "
    "text_hash, findings, vocabulary_version}; each finding "
    "carries finding_id, class, rule_ref, span, and the quoted "
    "match.",
    {"text": _sp("Copy to screen, exactly as it would be sent.")},
    ["text"], _ann(True, idempotent=True),
    _out({"text": _sp("The input text, unmodified."),
          "text_unmodified": _bp("Always true."),
          "text_hash": _sp("Content hash of the text."),
          "findings": _ap("Vocabulary findings with spans.",
                          items={"type": "object"}),
          "vocabulary_version": _sp("Vocabulary pack version "
                                    "applied.")},
         ["text", "text_unmodified", "findings"]))

TOOL_DEFS["criteria_screen"] = (
    "Screen audience-targeting criteria against the closed, "
    "versioned criteria vocabulary: protected criteria refuse "
    "by name and known proxy criteria refuse with the proxy "
    "named. Use before building or sending to a targeted "
    "audience; use copy_screen instead for message wording. "
    "Read-only and constructive of nothing: on a refusal no "
    "partial audience is built (audience_built is always "
    "false). Fails closed with VOCABULARY_UNAVAILABLE when the "
    "vocabulary pack cannot be loaded. " + _CTXT + " Returns "
    "{criteria, refused, refusals, findings, audience_built, "
    "note}.",
    {"criteria": _sp("Targeting criteria text to screen, e.g. a "
                     "plain-language audience description.")},
    ["criteria"], _ann(True, idempotent=True),
    _out({"criteria": _sp("The criteria as supplied."),
          "refused": _bp("True when any refusal fired."),
          "refusals": _ap("Refusal classes: "
                          "PROTECTED_CRITERIA_REFUSED and/or "
                          "PROXY_CRITERIA_REFUSED.",
                          items={"type": "string"}),
          "findings": _ap("Findings naming the matched class and, "
                          "for proxies, the proxy named.",
                          items={"type": "object"}),
          "audience_built": _bp("Always false.")},
         ["criteria", "refused", "refusals"]))

TOOL_DEFS["consent_record_verify"] = (
    "Verify a consent record or an evidence pack offline, on a "
    "separate code path from the sealer that produced it. Use "
    "to audit integrity before relying on a record or pack; use "
    "consent_record_read or pack_retrieve to read the artifact "
    "itself. Read-only: verification changes nothing. mode=RECORD "
    "checks the record's hash and seal signature, that its "
    "provenance class does not exceed its stored evidence, and "
    "class vocabulary validity. mode=PACK checks every entry's "
    "hash chain, that SEND entries carry a full six-step PASS "
    "transcript, that REFUSAL entries name a refusal class, the "
    "pack seal, and re-checks revocation honor-deadline "
    "arithmetic under the exact rule-pack version pinned at send "
    "time (hash-compared against the archive). A missing "
    "artifact is a verdict, not an error: verdict INCOMPLETE "
    "with the missing items listed. Available on both the agent "
    "and operator surfaces. " + _CTXT + " Returns {verdict, "
    "discrepancies, missing} with verdict VERIFIED, FAILED, or "
    "INCOMPLETE — enumerated discrepancies, never a score.",
    {"mode": _sp("RECORD or PACK; anything else is refused."),
     "record_id": _sp("RECORD mode: stored record id to verify "
                      "when 'record' is not supplied."),
     "record": _op("RECORD mode: a record object supplied "
                   "directly for offline verification, taking "
                   "precedence over record_id."),
     "pack_id": _sp("PACK mode: stored pack id to verify when "
                    "'pack' is not supplied."),
     "pack": _op("PACK mode: a pack object supplied directly "
                 "for offline verification, taking precedence "
                 "over pack_id.")},
    ["mode"], _ann(True, idempotent=True),
    _out({"verdict": _sp("VERIFIED, FAILED, or INCOMPLETE."),
          "discrepancies": _ap("Enumerated integrity problems; "
                               "empty when verified.",
                               items={"type": "string"}),
          "missing": _ap("Items needed for a complete verdict.",
                         items={"type": "string"})},
         ["verdict", "discrepancies", "missing"]))

TOOL_DEFS["mandate_create"] = (
    "Create a brokerage mandate on the OPERATOR surface only "
    "(this surface exposes no send tools). Use to authorize a "
    "brokerage's seats and channels before any lead_intake "
    "under the mandate; agent-surface callers cannot create "
    "mandates. Mutating and persistent: mints the mandate with "
    "the active rule-pack version pinned. The officer signature "
    "must verify over the officer plus brokerage_id before "
    "anything is stored — an unsigned or badly signed request "
    "refuses with MANDATE_UNSIGNED. vendor_lead_posture is a "
    "closed vocabulary (NARROW_FIRST_CONTACT_ONLY or "
    "REFUSE_ALL); an unknown posture refuses at creation and is "
    "never stored. " + _CTXT + " Returns {mandate_id, "
    "rule_version, vendor_lead_posture}.",
    {"brokerage_id": _sp("Brokerage the mandate authorizes; "
                         "part of the signed payload."),
     "officer": _sp("Brokerage officer creating the mandate; "
                    "part of the signed payload."),
     "officer_sig": _sp("Officer signature over {mandate_officer: "
                        "officer, brokerage_id}; verified before "
                        "the mandate is minted."),
     "broker_of_record": _sp("Broker of record named on evidence "
                             "packs; defaults to brokerage_id."),
     "seats": _ap("Sending identities covered by this mandate, "
                  "as a list of strings. A sender not in seats "
                  "fails every send gate under this mandate.",
                  items={"type": "string"}),
     "channels": _ap("Channels the mandate covers: voice, text, "
                     "email; defaults to all three.",
                     items={"type": "string"}),
     "vendor_lead_posture": _sp("NARROW_FIRST_CONTACT_ONLY or "
                                "REFUSE_ALL; defaults to the rule "
                                "pack's posture. Unknown values "
                                "refuse creation."),
     "state_overlays": _ap("State overlay identifiers applied to "
                           "the mandate, as a list of strings.",
                           items={"type": "string"}),
     "at_time": _sp("ISO 8601 creation time; defaults to the "
                    "server clock.")},
    ["brokerage_id", "officer", "officer_sig"], _ann(False),
    _out({"mandate_id": _sp("Assigned mandate id, e.g. "
                            "'MND-0001'."),
          "rule_version": _op("Rule pack reference pinned: "
                              "{set_id, version, hash, set_by}."),
          "vendor_lead_posture": _sp("Posture stored on the "
                                     "mandate.")},
         ["mandate_id", "vendor_lead_posture"]))

TOOL_DEFS["pack_retrieve"] = (
    "Retrieve one sealed evidence pack by pack_id on the "
    "OPERATOR surface only, for the broker of record. Use to "
    "audit the defense file for a lead: every send and every "
    "refusal sealed as a hash-chained, signed entry with its "
    "full gate transcript. Use consent_record_verify with "
    "mode=PACK instead to check a pack's integrity without "
    "reading it here. Read-only. Packs are created lazily by "
    "the first send, refusal, or revocation for a lead under a "
    "mandate, so a lead with no gated activity has no pack. "
    "Fails with PACK_NOT_FOUND for an unknown pack_id. " +
    _CTXT + " Returns the full pack object.",
    {"pack_id": _sp("Pack id, e.g. 'PACK-0001'.")},
    ["pack_id"], _ann(True, idempotent=True),
    _out({"pack_id": _sp("Pack id."),
          "session_id": _sp("Session the pack seals."),
          "mandate_id": _sp("Mandate the pack belongs to."),
          "lead_id": _sp("Lead the pack belongs to."),
          "broker_of_record": _sp("Broker named on the pack."),
          "entries": _ap("Hash-chained sealed entries: sends, "
                         "refusals, revocations, clarifications.",
                         items={"type": "object"}),
          "revocations": _ap("Revocation entries mirrored on "
                             "the pack.",
                             items={"type": "object"}),
          "rule_versions_used": _ap("Pinned rule-pack references "
                                    "used by the pack's entries.",
                                    items={"type": "object"}),
          "hash": _sp("Pack seal hash."),
          "herald_sig": _sp("Seal signature over the pack hash."),
          "sealed_at": {"type": ["string", "null"],
                        "description": "ISO 8601 time of the last "
                        "entry, or null for an empty pack."}},
         ["pack_id", "entries"]))


def tool_list():
    names = AGENT_TOOLS if SURFACE == "agent" else OPERATOR_TOOLS
    tools = []
    for n in names:
        desc, props, required, ann, out = TOOL_DEFS[n]
        tools.append({
            "name": n, "description": desc,
            "inputSchema": {"type": "object", "properties": props,
                            "required": required},
            "annotations": ann, "outputSchema": out})
    return tools


def dispatch(state, name, args):
    allowed = AGENT_TOOLS if SURFACE == "agent" else OPERATOR_TOOLS
    if name not in allowed:
        raise ToolError("UNKNOWN_TOOL",
                        f"tool {name} is not on the {SURFACE} surface")
    if name == "mandate_create":
        return eng.mandate_create(state, args)
    if name == "pack_retrieve":
        return pack_retrieve(state, args)
    return eng.call_tool(state, name, args)


def handle(state, msg):
    method = msg.get("method")
    rid = msg.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "eclipse-covenant-mcp",
                           "version": "0.1.0"}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid,
                "result": {"tools": tool_list()}}
    if method == "tools/call":
        params = msg.get("params") or {}
        if not isinstance(params, dict):
            params = {}
        try:
            result = dispatch(state, params.get("name"),
                              params.get("arguments") or {})
            save_state(state)
            return {"jsonrpc": "2.0", "id": rid, "result": {
                "content": [{"type": "text",
                             "text": json.dumps(result)}]}}
        except ToolError as exc:
            payload = {"refusal": exc.refusal, "body": exc.body}
            payload.update(exc.extra)
            return {"jsonrpc": "2.0", "id": rid, "result": {
                "isError": True,
                "content": [{"type": "text",
                             "text": json.dumps(payload)}]}}
        except Exception as exc:  # noqa: BLE001 — containment, by design
            # The stdio process must NEVER die on input: any unexpected
            # engine error is contained as a named fail-closed refusal.
            payload = {"refusal": "INTERNAL_ERROR",
                       "body": f"unexpected error contained and refused "
                               f"by name: {type(exc).__name__}"}
            return {"jsonrpc": "2.0", "id": rid, "result": {
                "isError": True,
                "content": [{"type": "text",
                             "text": json.dumps(payload)}]}}
    return {"jsonrpc": "2.0", "id": rid,
            "error": {"code": -32601, "message": f"unknown {method}"}}


def main():
    state = load_state()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        if not isinstance(msg, dict):
            resp = {"jsonrpc": "2.0", "id": None, "error": {
                "code": -32600,
                "message": "invalid request: expected a JSON object"}}
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
            continue
        if str(msg.get("method", "")).startswith("notifications/"):
            continue
        try:
            resp = handle(state, msg)
        except Exception as exc:  # noqa: BLE001 — containment, by design
            resp = {"jsonrpc": "2.0", "id": msg.get("id"), "error": {
                "code": -32603,
                "message": f"internal error contained: "
                           f"{type(exc).__name__}"}}
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()

# Eclipse Covenant MCP · © 2026 Cyan Eclipse Technologies LLC · cetech.ai
