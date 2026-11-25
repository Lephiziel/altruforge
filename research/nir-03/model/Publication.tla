---------------------------- MODULE Publication ----------------------------
EXTENDS Naturals

CONSTANTS AtomicRefGuard, UniqueOpen, BlindReplay, AllowDrift, MaxCrashes

VARIABLES ledger, alive, crashes, head, base, actorWrote, preflight,
          submitted, inFlight, effects, wrongArtifact, observed, receipt

vars == <<ledger, alive, crashes, head, base, actorWrote, preflight,
          submitted, inFlight, effects, wrongArtifact, observed, receipt>>

Pending == ledger \in {"Pending", "Unknown"}
ExactRefs == head = "Candidate" /\ base = "VerifiedBase"

Init ==
    /\ ledger = "Unsealed"
    /\ alive = TRUE
    /\ crashes = 0
    /\ head = "Missing"
    /\ base = "VerifiedBase"
    /\ actorWrote = FALSE
    /\ preflight = FALSE
    /\ submitted = 0
    /\ inFlight = FALSE
    /\ effects = 0
    /\ wrongArtifact = FALSE
    /\ observed = FALSE
    /\ receipt = FALSE

SealIntent ==
    /\ alive /\ ledger = "Unsealed"
    /\ ledger' = "Pending"
    /\ UNCHANGED <<alive, crashes, head, base, actorWrote, preflight,
                   submitted, inFlight, effects, wrongArtifact, observed, receipt>>

InstallCandidate ==
    /\ alive /\ Pending /\ head = "Missing" /\ base = "VerifiedBase"
    /\ head' = "Candidate"
    /\ UNCHANGED <<ledger, alive, crashes, base, actorWrote, preflight,
                   submitted, inFlight, effects, wrongArtifact, observed, receipt>>

Preflight ==
    /\ alive /\ Pending /\ ExactRefs /\ ~preflight
    /\ preflight' = TRUE
    /\ UNCHANGED <<ledger, alive, crashes, head, base, actorWrote,
                   submitted, inFlight, effects, wrongArtifact, observed, receipt>>

Dispatch ==
    /\ alive /\ ledger = "Pending" /\ preflight /\ ~inFlight
    /\ submitted = 0 \/ (BlindReplay /\ submitted = 1)
    /\ submitted' = submitted + 1
    /\ inFlight' = TRUE
    /\ UNCHANGED <<ledger, alive, crashes, head, base, actorWrote, preflight,
                   effects, wrongArtifact, observed, receipt>>

Settle ==
    /\ inFlight
    /\ inFlight' = FALSE
    /\ IF (AtomicRefGuard /\ ~ExactRefs) \/ (UniqueOpen /\ effects > 0)
       THEN UNCHANGED <<effects, wrongArtifact>>
       ELSE /\ effects' = effects + 1
            /\ wrongArtifact' = (wrongArtifact \/ ~ExactRefs)
    /\ UNCHANGED <<ledger, alive, crashes, head, base, actorWrote, preflight,
                   submitted, observed, receipt>>

Observe ==
    /\ alive /\ Pending /\ effects = 1 /\ ExactRefs /\ ~observed
    /\ observed' = TRUE
    /\ UNCHANGED <<ledger, alive, crashes, head, base, actorWrote, preflight,
                   submitted, inFlight, effects, wrongArtifact, receipt>>

PersistCompletion ==
    /\ alive /\ Pending /\ observed
    /\ ledger' = "Complete"
    /\ receipt' = TRUE
    /\ UNCHANGED <<alive, crashes, head, base, actorWrote, preflight,
                   submitted, inFlight, effects, wrongArtifact, observed>>

RecordUnknown ==
    /\ alive /\ ledger = "Pending" /\ crashes > 0 /\ submitted > 0
    /\ effects = 0
    /\ ledger' = "Unknown"
    /\ UNCHANGED <<alive, crashes, head, base, actorWrote, preflight,
                   submitted, inFlight, effects, wrongArtifact, observed, receipt>>

BlockConflict ==
    /\ alive /\ Pending
    /\ actorWrote \/ base # "VerifiedBase" \/ effects > 1
    /\ ledger' = "Blocked"
    /\ UNCHANGED <<alive, crashes, head, base, actorWrote, preflight,
                   submitted, inFlight, effects, wrongArtifact, observed, receipt>>

Crash ==
    /\ alive /\ crashes < MaxCrashes
    /\ ledger \in {"Unsealed", "Pending", "Unknown"}
    /\ alive' = FALSE
    /\ crashes' = crashes + 1
    /\ preflight' = FALSE
    /\ observed' = FALSE
    /\ UNCHANGED <<ledger, head, base, actorWrote, submitted, inFlight,
                   effects, wrongArtifact, receipt>>

Restart ==
    /\ ~alive
    /\ alive' = TRUE
    /\ UNCHANGED <<ledger, crashes, head, base, actorWrote, preflight,
                   submitted, inFlight, effects, wrongArtifact, observed, receipt>>

DriftHead ==
    /\ AllowDrift /\ head = "Candidate"
    /\ head' = "Other"
    /\ actorWrote' = TRUE
    /\ UNCHANGED <<ledger, alive, crashes, base, preflight, submitted,
                   inFlight, effects, wrongArtifact, observed, receipt>>

DriftBase ==
    /\ AllowDrift /\ base = "VerifiedBase"
    /\ base' = "OtherBase"
    /\ UNCHANGED <<ledger, alive, crashes, head, actorWrote, preflight,
                   submitted, inFlight, effects, wrongArtifact, observed, receipt>>

Next ==
    \/ SealIntent \/ InstallCandidate \/ Preflight \/ Dispatch \/ Settle
    \/ Observe \/ PersistCompletion \/ RecordUnknown \/ BlockConflict
    \/ Crash \/ Restart \/ DriftHead \/ DriftBase

Spec == Init /\ [][Next]_vars

FairSpec ==
    /\ Spec
    /\ WF_vars(SealIntent)
    /\ WF_vars(InstallCandidate)
    /\ WF_vars(Preflight)
    /\ WF_vars(Dispatch)
    /\ WF_vars(Settle)
    /\ WF_vars(Observe)
    /\ WF_vars(PersistCompletion)
    /\ WF_vars(Restart)

TypeOK ==
    /\ ledger \in {"Unsealed", "Pending", "Unknown", "Blocked", "Complete"}
    /\ alive \in BOOLEAN
    /\ crashes \in 0..MaxCrashes
    /\ head \in {"Missing", "Candidate", "Other"}
    /\ base \in {"VerifiedBase", "OtherBase"}
    /\ actorWrote \in BOOLEAN
    /\ preflight \in BOOLEAN
    /\ submitted \in 0..2
    /\ inFlight \in BOOLEAN
    /\ effects \in 0..submitted
    /\ wrongArtifact \in BOOLEAN
    /\ observed \in BOOLEAN
    /\ receipt \in BOOLEAN

IntentBeforeEffects ==
    (head # "Missing" \/ submitted > 0) => ledger # "Unsealed"

ForeignHeadPreserved == actorWrote => head = "Other"
VerifiedAtCreation == ~wrongArtifact
AtMostOneEffect == effects <= 1
CompletionHasReceipt == ledger = "Complete" => receipt /\ observed /\ effects >= 1
EventuallyComplete == <> (ledger = "Complete")

=============================================================================
