-------------------------- MODULE CandidatePublication --------------------------
EXTENDS Naturals, FiniteSets, TLC

CONSTANTS CandidateSha, BaseSha, DriftSha, VerificationDigest, RunId, NoIdentity,
          RefValues
ASSUME CandidateSha \in RefValues
ASSUME BaseSha \in RefValues
ASSUME DriftSha \in RefValues
ASSUME CandidateSha # BaseSha
ASSUME CandidateSha # DriftSha
ASSUME BaseSha # DriftSha

VARIABLES phase, intentRun, intentHead, intentBase, intentVerification,
          remoteHead, remotePRRun, remotePRBase, remotePRHead,
          remoteStatusSha, remoteStatusVerification, observed
vars == <<phase, intentRun, intentHead, intentBase, intentVerification,
          remoteHead, remotePRRun, remotePRBase, remotePRHead,
          remoteStatusSha, remoteStatusVerification, observed>>

Phases == {"idle", "intent", "recovering", "complete", "conflict", "unknown"}
ExpectedPRPresent ==
    /\ remotePRRun = RunId
    /\ remotePRBase = BaseSha
    /\ remotePRHead = CandidateSha
ExpectedStatusPresent ==
    /\ remoteStatusSha = CandidateSha
    /\ remoteStatusVerification = VerificationDigest

Init ==
    /\ phase = "idle"
    /\ intentRun = NoIdentity
    /\ intentHead = NoIdentity
    /\ intentBase = NoIdentity
    /\ intentVerification = NoIdentity
    /\ remoteHead = BaseSha
    /\ remotePRRun = NoIdentity
    /\ remotePRBase = NoIdentity
    /\ remotePRHead = NoIdentity
    /\ remoteStatusSha = NoIdentity
    /\ remoteStatusVerification = NoIdentity
    /\ observed = FALSE

PersistIntent ==
    /\ phase = "idle"
    /\ phase' = "intent"
    /\ intentRun' = RunId
    /\ intentHead' = CandidateSha
    /\ intentBase' = BaseSha
    /\ intentVerification' = VerificationDigest
    /\ UNCHANGED <<remoteHead, remotePRRun, remotePRBase, remotePRHead,
                   remoteStatusSha, remoteStatusVerification, observed>>

DispatchRef ==
    /\ phase \in {"intent", "recovering"}
    /\ intentHead = CandidateSha
    /\ remoteHead = BaseSha
    /\ remoteHead' = CandidateSha
    /\ phase' = "recovering"
    /\ observed' = FALSE
    /\ UNCHANGED <<intentRun, intentHead, intentBase, intentVerification,
                   remotePRRun, remotePRBase, remotePRHead,
                   remoteStatusSha, remoteStatusVerification>>

DispatchPR ==
    /\ phase \in {"intent", "recovering"}
    /\ intentRun = RunId
    /\ intentHead = CandidateSha
    /\ intentBase = BaseSha
    /\ remoteHead = CandidateSha
    /\ remotePRRun = NoIdentity
    /\ remotePRRun' = RunId
    /\ remotePRBase' = BaseSha
    /\ remotePRHead' = CandidateSha
    /\ phase' = "recovering"
    /\ observed' = FALSE
    /\ UNCHANGED <<intentRun, intentHead, intentBase, intentVerification,
                   remoteHead, remoteStatusSha, remoteStatusVerification>>

DispatchStatus ==
    /\ phase \in {"intent", "recovering"}
    /\ intentHead = CandidateSha
    /\ intentVerification = VerificationDigest
    /\ remoteStatusSha = NoIdentity
    /\ remoteStatusSha' = CandidateSha
    /\ remoteStatusVerification' = VerificationDigest
    /\ phase' = "recovering"
    /\ observed' = FALSE
    /\ UNCHANGED <<intentRun, intentHead, intentBase, intentVerification,
                   remoteHead, remotePRRun, remotePRBase, remotePRHead>>

ConcurrentDrift ==
    /\ phase \in {"intent", "recovering"}
    /\ remoteHead = BaseSha
    /\ remoteHead' = DriftSha
    /\ phase' = "recovering"
    /\ observed' = FALSE
    /\ UNCHANGED <<intentRun, intentHead, intentBase, intentVerification,
                   remotePRRun, remotePRBase, remotePRHead,
                   remoteStatusSha, remoteStatusVerification>>

Crash ==
    /\ phase \in {"intent", "recovering"}
    /\ phase' = "unknown"
    /\ observed' = FALSE
    /\ UNCHANGED <<intentRun, intentHead, intentBase, intentVerification,
                   remoteHead, remotePRRun, remotePRBase, remotePRHead,
                   remoteStatusSha, remoteStatusVerification>>

Resume ==
    /\ phase = "unknown"
    /\ phase' = "recovering"
    /\ observed' = FALSE
    /\ UNCHANGED <<intentRun, intentHead, intentBase, intentVerification,
                   remoteHead, remotePRRun, remotePRBase, remotePRHead,
                   remoteStatusSha, remoteStatusVerification>>

ObserveComplete ==
    /\ phase \in {"recovering", "unknown"}
    /\ remoteHead = CandidateSha
    /\ ExpectedPRPresent
    /\ ExpectedStatusPresent
    /\ phase' = "complete"
    /\ observed' = TRUE
    /\ UNCHANGED <<intentRun, intentHead, intentBase, intentVerification,
                   remoteHead, remotePRRun, remotePRBase, remotePRHead,
                   remoteStatusSha, remoteStatusVerification>>

ObserveConflict ==
    /\ phase \in {"recovering", "unknown"}
    /\ remoteHead = DriftSha
    /\ phase' = "conflict"
    /\ observed' = TRUE
    /\ UNCHANGED <<intentRun, intentHead, intentBase, intentVerification,
                   remoteHead, remotePRRun, remotePRBase, remotePRHead,
                   remoteStatusSha, remoteStatusVerification>>

ObserveIncomplete ==
    /\ phase \in {"recovering", "unknown"}
    /\ remoteHead # DriftSha
    /\ ~((remoteHead = CandidateSha) /\ ExpectedPRPresent /\ ExpectedStatusPresent)
    /\ phase' = "recovering"
    /\ observed' = TRUE
    /\ UNCHANGED <<intentRun, intentHead, intentBase, intentVerification,
                   remoteHead, remotePRRun, remotePRBase, remotePRHead,
                   remoteStatusSha, remoteStatusVerification>>

Next == PersistIntent \/ DispatchRef \/ DispatchPR \/ DispatchStatus
        \/ ConcurrentDrift \/ Crash \/ Resume \/ ObserveComplete
        \/ ObserveConflict \/ ObserveIncomplete

Spec == Init /\ [][Next]_vars
RecoveryNext == PersistIntent \/ DispatchRef \/ DispatchPR \/ DispatchStatus
                \/ ConcurrentDrift \/ Resume \/ ObserveComplete
                \/ ObserveConflict \/ ObserveIncomplete
FairRecoverySpec == Init /\ [][RecoveryNext]_vars
                    /\ WF_vars(DispatchRef) /\ WF_vars(DispatchPR)
                    /\ WF_vars(DispatchStatus) /\ WF_vars(ObserveComplete)
                    /\ WF_vars(ObserveConflict) /\ WF_vars(ObserveIncomplete)
                    /\ WF_vars(Resume)

TypeOK ==
    /\ phase \in Phases
    /\ intentRun \in {NoIdentity, RunId}
    /\ intentHead \in {NoIdentity, CandidateSha}
    /\ intentBase \in {NoIdentity, BaseSha}
    /\ intentVerification \in {NoIdentity, VerificationDigest}
    /\ remoteHead \in RefValues
    /\ remotePRRun \in {NoIdentity, RunId}
    /\ remotePRBase \in {NoIdentity, BaseSha}
    /\ remotePRHead \in {NoIdentity, CandidateSha}
    /\ remoteStatusSha \in {NoIdentity, CandidateSha}
    /\ remoteStatusVerification \in {NoIdentity, VerificationDigest}
    /\ observed \in BOOLEAN

IntentIdentityStable ==
    phase # "idle" =>
      /\ intentRun = RunId
      /\ intentHead = CandidateSha
      /\ intentBase = BaseSha
      /\ intentVerification = VerificationDigest

CompleteHasExactEvidence ==
    phase = "complete" =>
      /\ intentRun = RunId
      /\ intentHead = CandidateSha
      /\ intentBase = BaseSha
      /\ intentVerification = VerificationDigest
      /\ remoteHead = CandidateSha
      /\ ExpectedPRPresent
      /\ ExpectedStatusPresent
      /\ observed = TRUE

RemoteEffectIdentitiesStayBound ==
    /\ (remotePRRun # NoIdentity =>
        /\ remotePRRun = RunId
        /\ remotePRBase = BaseSha
        /\ remotePRHead = CandidateSha)
    /\ (remoteStatusSha # NoIdentity =>
        /\ remoteStatusSha = CandidateSha
        /\ remoteStatusVerification = VerificationDigest)

EventuallyTerminal == (phase = "intent" \/ phase = "recovering" \/ phase = "unknown")
                     ~> (phase = "complete" \/ phase = "conflict")

=============================================================================
