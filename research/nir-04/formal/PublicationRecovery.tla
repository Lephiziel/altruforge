-------------------------- MODULE PublicationRecovery --------------------------
EXTENDS Naturals, FiniteSets, Sequences, TLC

CONSTANTS Publishers, Artifacts, Base, NoVal, NoReq,
          Dedup, CAS, Fence, ReadMode, BindDigest, SafeAbsence, RequireFresh, RetryOnly
ASSUME Publishers = {"p1", "p2"}
ASSUME Artifacts = {"a1", "a2"}
ASSUME Base \notin Artifacts
ASSUME NoVal \notin Artifacts \cup {Base}
ASSUME NoReq \notin {"r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12"}
ASSUME ReadMode \in {"fresh", "stale", "inconsistent", "unavailable"}

VARIABLES up, durable, reqs, pending, ack, ref, refOwner, objects, statuses, epochs,
          fenceClock, highestFence, seen,
          observedRef, observedReview, observedStatus, observationFresh, decision,
          classified, ticks
vars == <<up, durable, reqs, pending, ack, ref, refOwner, objects, statuses, epochs,
          fenceClock, highestFence, seen,
          observedRef, observedReview, observedStatus, observationFresh, decision,
          classified, ticks>>

Phases == {"empty", "intent", "unknown", "not_executed", "complete", "conflict"}
Reqs == {NoReq, "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12"}
Operations == {"ref", "review", "status"}
Kinds == {"none"} \cup Operations
ReqIds == Reqs \ {NoReq}
RefVals == {Base} \cup Artifacts
Other(a) == CHOOSE b \in Artifacts : b # a
Receipt(a) == IF a = "a1" THEN "receipt1" ELSE "receipt2"
StaleValue(p) ==
  IF \E old \in seen[p] : old # ref
  THEN CHOOSE old \in seen[p] : old # ref
  ELSE Base
ExpectedObject(p) ==
  \E x \in objects : x.owner = p /\ x.art = durable[p].art
                        /\ x.receipt = durable[p].receipt
ExpectedStatus(p) ==
  \E x \in statuses : x.owner = p /\ x.art = durable[p].art
                         /\ x.receipt = durable[p].receipt
SentCount(p, kind) == Cardinality({r \in ReqIds : reqs[r].owner = p /\
                          reqs[r].kind = kind /\ reqs[r].state # "unused"})
HasPending(p) == \E r \in pending : reqs[r].owner = p
HasPendingKind(p, kind) == \E r \in pending : reqs[r].owner = p /\ reqs[r].kind = kind
HasEverSent(p) == \E r \in ReqIds : reqs[r].owner = p /\ reqs[r].state # "unused"
ObservedSatisfied(p, kind) ==
  IF kind = "ref" THEN observedRef[p] = durable[p].art
  ELSE IF kind = "review" THEN observedReview[p]
  ELSE observedStatus[p]

Init ==
  /\ up = [p \in Publishers |-> TRUE]
  /\ durable = [p \in Publishers |-> [phase |-> "empty", art |-> NoVal,
                                      verified |-> FALSE, receipt |-> NoVal,
                                      key |-> NoVal,
                                      epoch |-> 0]]
  /\ reqs = [r \in Reqs |-> [owner |-> "p1", kind |-> "none", art |-> NoVal,
                               receipt |-> NoVal, key |-> NoVal,
                               epoch |-> 0, state |-> "unused"]]
  /\ pending = {}
  /\ ack = [r \in Reqs |-> "none"]
  /\ ref = Base
  /\ refOwner = NoVal
  /\ objects = {}
  /\ statuses = {}
  /\ epochs = [p \in Publishers |-> IF p = "p1" THEN 0 ELSE 1]
  /\ fenceClock = 1
  /\ highestFence = 0
  /\ seen = [p \in Publishers |-> {}]
  /\ observedRef = [p \in Publishers |-> NoVal]
  /\ observedReview = [p \in Publishers |-> FALSE]
  /\ observedStatus = [p \in Publishers |-> FALSE]
  /\ observationFresh = [p \in Publishers |-> FALSE]
  /\ decision = [p \in Publishers |-> [ref |-> Base, review |-> FALSE, status |-> FALSE,
                                            pending |-> FALSE, fresh |-> FALSE]]
  /\ classified = [p \in Publishers |-> "empty"]
  /\ ticks = 0

Persist(p, a) ==
  /\ p \in Publishers /\ a \in Artifacts
  /\ up[p] /\ durable[p].phase = "empty"
  /\ durable' = [durable EXCEPT ![p] = [phase |-> "intent", art |-> a,
                                        verified |-> TRUE,
                                        receipt |-> Receipt(a),
                                        key |-> IF Dedup THEN p ELSE NoVal,
                                        epoch |-> epochs[p]]]
  /\ classified' = [classified EXCEPT ![p] = "intent"]
  /\ UNCHANGED <<up, reqs, pending, ack, ref, refOwner, objects, epochs, fenceClock, highestFence, seen,
                 observedRef, observedReview, observedStatus,
                 observationFresh, decision, statuses, ticks>>

Dispatch(p, r, kind) ==
  /\ p \in Publishers /\ r \in ReqIds
  /\ kind \in Operations
  /\ up[p] /\ durable[p].phase \in {"intent", "unknown"}
  /\ (RetryOnly \/ (observationFresh[p] /\ ~ObservedSatisfied(p, kind)))
  /\ (RetryOnly \/ ~HasPendingKind(p, kind))
  /\ SentCount(p, kind) < 2
  /\ r \notin pending /\ reqs[r].state = "unused"
  /\ reqs' = [reqs EXCEPT ![r] = [owner |-> p, kind |-> kind,
                                  art |-> durable[p].art,
                                  receipt |-> durable[p].receipt,
                                  key |-> durable[p].key, epoch |-> epochs[p],
                                  state |-> "pending"]]
  /\ pending' = pending \cup {r}
  /\ ack' = [ack EXCEPT ![r] = "delayed"]
  /\ durable' = [durable EXCEPT ![p].phase = "intent"]
  /\ classified' = [classified EXCEPT ![p] = "intent"]
  /\ UNCHANGED <<up, ref, refOwner, objects, statuses, epochs, fenceClock, highestFence, seen, observedRef,
                 observedReview, observedStatus, observationFresh, decision, ticks>>

Settle(r) ==
  /\ r \in pending
  /\ LET p == reqs[r].owner
         a == reqs[r].art
         allowed == IF Fence THEN reqs[r].epoch >= highestFence ELSE TRUE
         baseOK == IF CAS THEN ref = Base ELSE TRUE
         dup == Dedup /\ \E x \in objects : x.key = reqs[r].key
         statusDup == Dedup /\ \E x \in statuses : x.key = reqs[r].key
     IN /\ reqs' = [reqs EXCEPT ![r].state = "settled"]
        /\ pending' = pending \ {r}
        /\ ref' = IF reqs[r].kind = "ref" /\ allowed /\ baseOK
                    THEN IF BindDigest THEN a ELSE Other(a)
                    ELSE ref
        /\ refOwner' = IF reqs[r].kind = "ref" /\ allowed /\ baseOK
                          THEN p ELSE refOwner
        /\ objects' = IF reqs[r].kind = "review" /\ allowed /\ ~dup
                         THEN objects \cup {[owner |-> p, art |-> a,
                                              receipt |-> reqs[r].receipt,
                                              key |-> reqs[r].key, req |-> r]}
                         ELSE objects
        /\ statuses' = IF reqs[r].kind = "status" /\ allowed /\ ~statusDup
                          THEN statuses \cup {[owner |-> p, art |-> a,
                                                receipt |-> reqs[r].receipt,
                                                key |-> reqs[r].key, req |-> r]}
                          ELSE statuses
        /\ highestFence' = IF Fence /\ allowed /\ reqs[r].epoch > highestFence
                              THEN reqs[r].epoch ELSE highestFence
  /\ ticks' = ticks + 1
  /\ observationFresh' = [p \in Publishers |-> FALSE]
  /\ UNCHANGED <<up, durable, ack, epochs, fenceClock, seen, observedRef,
                 observedReview, observedStatus, decision, classified>>

DeliverAck(r) ==
  /\ r \in Reqs \ {NoReq}
  /\ reqs[r].state = "settled"
  /\ ack[r] = "delayed"
  /\ ack' = [ack EXCEPT ![r] = "received"]
  /\ UNCHANGED <<up, durable, reqs, pending, ref, refOwner, objects, epochs, fenceClock, highestFence, seen,
                 observedRef, observedReview, observedStatus, statuses,
                 observationFresh, decision, classified, ticks>>

LoseAck(r) ==
  /\ r \in Reqs \ {NoReq}
  /\ reqs[r].state = "settled"
  /\ ack[r] = "delayed"
  /\ ack' = [ack EXCEPT ![r] = "lost"]
  /\ UNCHANGED <<up, durable, reqs, pending, ref, refOwner, objects, epochs, fenceClock, highestFence, seen,
                 observedRef, observedReview, observedStatus, statuses,
                 observationFresh, decision, classified, ticks>>

Crash(p) ==
  /\ p \in Publishers /\ up[p]
  /\ up' = [up EXCEPT ![p] = FALSE]
  /\ durable' = [durable EXCEPT ![p].phase =
                   IF @ = "empty" \/ @ = "complete" \/ @ = "conflict" \/ @ = "not_executed" THEN @ ELSE "unknown"]
  /\ classified' = [classified EXCEPT ![p] =
                      IF @ = "empty" \/ @ = "complete" \/ @ = "conflict" \/ @ = "not_executed" THEN @ ELSE "unknown"]
  /\ observationFresh' = [observationFresh EXCEPT ![p] = FALSE]
  /\ UNCHANGED <<reqs, pending, ack, ref, refOwner, objects, statuses, epochs, fenceClock, highestFence, seen, observedRef,
                 observedReview, observedStatus, decision, ticks>>

Recover(p) ==
  /\ p \in Publishers /\ ~up[p] /\ fenceClock < 5
  /\ up' = [up EXCEPT ![p] = TRUE]
  /\ fenceClock' = fenceClock + 1
  /\ epochs' = [epochs EXCEPT ![p] = fenceClock + 1]
  /\ durable' = [durable EXCEPT ![p].phase =
                   IF @ = "unknown" THEN "intent" ELSE @]
  /\ classified' = [classified EXCEPT ![p] =
                      IF @ = "unknown" THEN "intent" ELSE @]
  /\ UNCHANGED <<reqs, pending, ack, ref, refOwner, objects, statuses, highestFence, seen, observedRef,
                 observedReview, observedStatus, observationFresh, decision, ticks>>

Observe(p) ==
  /\ p \in Publishers /\ up[p]
  /\ durable[p].phase \in {"intent", "unknown"}
  /\ LET available == ReadMode # "unavailable"
         v == IF ReadMode = "inconsistent" /\ p = "p2" THEN Base
              ELSE IF ReadMode = "stale" /\ ticks > 0 THEN StaleValue(p) ELSE ref
     IN /\ observedRef' = [observedRef EXCEPT ![p] = IF available THEN v ELSE NoVal]
        /\ observationFresh' = [observationFresh EXCEPT ![p] =
             available /\ (ReadMode = "fresh" \/ (ReadMode = "stale" /\ ticks = 0)
                           )]
        /\ observedReview' = [observedReview EXCEPT ![p] =
             available /\ ExpectedObject(p)]
        /\ observedStatus' = [observedStatus EXCEPT ![p] =
             available /\ ExpectedStatus(p)]
        /\ seen' = [seen EXCEPT ![p] = @ \cup (IF available THEN {v} ELSE {})]
        /\ decision' = [decision EXCEPT ![p] = [ref |-> ref,
              review |-> ExpectedObject(p), status |-> ExpectedStatus(p),
              pending |-> HasPending(p),
              fresh |-> available /\ (ReadMode = "fresh" \/ (ReadMode = "stale" /\ ticks = 0))]]
        /\ classified' = [classified EXCEPT ![p] =
             IF ~available THEN "unknown"
             ELSE IF v = durable[p].art /\ durable[p].verified
                       /\ observedReview'[p] /\ observedStatus'[p]
                       /\ (~RequireFresh \/ observationFresh'[p])
                  THEN "complete"
             ELSE IF (~RequireFresh \/ observationFresh'[p]) /\ v # Base /\ v # durable[p].art THEN "conflict"
             ELSE IF (~RequireFresh \/ observationFresh'[p])
                       /\ HasEverSent(p) /\ ~observedReview'[p] /\ ~observedStatus'[p]
                       /\ (~HasPending(p) \/ ~SafeAbsence) THEN "not_executed"
             ELSE "unknown"]
        /\ durable' = [durable EXCEPT ![p].phase =
             IF ~available THEN "unknown"
             ELSE IF v = durable[p].art /\ durable[p].verified
                       /\ observedReview'[p] /\ observedStatus'[p]
                       /\ (~RequireFresh \/ observationFresh'[p])
                  THEN "complete"
             ELSE IF (~RequireFresh \/ observationFresh'[p]) /\ v # Base /\ v # durable[p].art THEN "conflict"
             ELSE IF (~RequireFresh \/ observationFresh'[p])
                       /\ HasEverSent(p) /\ ~observedReview'[p] /\ ~observedStatus'[p]
                       /\ (~HasPending(p) \/ ~SafeAbsence) THEN "not_executed"
             ELSE "unknown"]
  /\ UNCHANGED <<up, reqs, pending, ack, ref, refOwner, objects, statuses, epochs,
                 fenceClock, highestFence, ticks>>

Next ==
  \/ (\E p \in Publishers :
       (\E a \in Artifacts : Persist(p, a)) \/ Crash(p) \/ Recover(p) \/ Observe(p))
  \/ (\E p \in Publishers, r \in ReqIds,
        kind \in Operations : Dispatch(p, r, kind))
  \/ (\E r \in pending : Settle(r))
  \/ (\E r \in Reqs \ {NoReq} : DeliverAck(r) \/ LoseAck(r))

Spec == Init /\ [][Next]_vars

TerminalEventually ==
  \A p \in Publishers : HasEverSent(p)
                           ~> (durable[p].phase \in {"complete", "conflict", "not_executed"})

TerminalStableEventually ==
  \A p \in Publishers : HasEverSent(p)
                           ~> [] (durable[p].phase \in {"complete", "conflict", "not_executed"})

FairStrongSpec ==
  /\ Spec
  /\ <>[](\A p \in Publishers : up[p])
  /\ \A p \in Publishers : WF_vars(Observe(p))
  /\ \A r \in ReqIds : WF_vars(Settle(r))
  /\ \A p \in Publishers, kind \in Operations :
       WF_vars(\E r \in ReqIds : Dispatch(p, r, kind))

TypeOK ==
  /\ up \in [Publishers -> BOOLEAN]
  /\ durable \in [Publishers -> [phase : Phases, art : {NoVal} \cup Artifacts,
                 verified : BOOLEAN, receipt : {NoVal, "receipt1", "receipt2"},
                 key : {NoVal} \cup Publishers, epoch : 0..5]]
  /\ epochs \in [Publishers -> 0..5]
  /\ fenceClock \in 0..5
  /\ highestFence \in 0..5
  /\ ref \in RefVals
  /\ refOwner \in {NoVal} \cup Publishers
  /\ pending \subseteq Reqs
  /\ ack \in [Reqs -> {"none", "delayed", "received", "lost"}]
  /\ reqs \in [Reqs -> [owner : Publishers, kind : Kinds,
                         art : {NoVal} \cup Artifacts,
                         receipt : {NoVal, "receipt1", "receipt2"},
                         key : {NoVal} \cup Publishers, epoch : 0..5,
                         state : {"unused", "pending", "settled"}]]
  /\ objects \subseteq [owner : Publishers, art : Artifacts,
                         receipt : {"receipt1", "receipt2"},
                         key : {NoVal} \cup Publishers,
                         req : ReqIds]
  /\ statuses \subseteq [owner : Publishers, art : Artifacts,
                          receipt : {"receipt1", "receipt2"},
                          key : {NoVal} \cup Publishers,
                         req : ReqIds]
  /\ classified \in [Publishers -> Phases]
  /\ observedRef \in [Publishers -> {NoVal} \cup RefVals]
  /\ observedReview \in [Publishers -> BOOLEAN]
  /\ observedStatus \in [Publishers -> BOOLEAN]
  /\ observationFresh \in [Publishers -> BOOLEAN]
  /\ decision \in [Publishers -> [ref : RefVals, review : BOOLEAN, status : BOOLEAN,
                               pending : BOOLEAN, fresh : BOOLEAN]]
  /\ ticks \in 0..12

SoundComplete ==
  \A p \in Publishers : classified[p] = "complete" =>
    /\ durable[p].verified
    /\ durable[p].art = observedRef[p]
    /\ durable[p].receipt = Receipt(durable[p].art)
    /\ observedReview[p]
    /\ observedStatus[p]
    /\ decision[p].fresh
    /\ decision[p].ref = durable[p].art
    /\ decision[p].review /\ decision[p].status

ArtifactIntegrity ==
  ref = Base \/ (refOwner \in Publishers
    /\ ref = durable[refOwner].art /\ durable[refOwner].verified
    /\ \E r \in ReqIds : reqs[r].kind = "ref" /\ reqs[r].owner = refOwner
         /\ reqs[r].state = "settled" /\ reqs[r].art = ref
         /\ reqs[r].receipt = durable[refOwner].receipt)

SoundConflict ==
  \A p \in Publishers : classified[p] = "conflict" =>
    /\ decision[p].fresh /\ decision[p].ref # Base /\ decision[p].ref # durable[p].art

SoundNotExecuted ==
  \A p \in Publishers : classified[p] = "not_executed" =>
    /\ decision[p].fresh
    /\ decision[p].ref = Base
    /\ ~decision[p].review /\ ~decision[p].status
    /\ ~decision[p].pending

AuthorizedEffects ==
  \A x \in objects \cup statuses :
    /\ durable[x.owner].verified
    /\ x.art = durable[x.owner].art
    /\ x.receipt = durable[x.owner].receipt

LogicalUniqueness ==
  \A p \in Publishers :
    /\ Cardinality({x \in objects : x.owner = p}) <= 1
    /\ Cardinality({x \in statuses : x.owner = p}) <= 1

DedupUniqueness ==
  Dedup =>
    \A p \in Publishers :
      /\ Cardinality({x \in objects : x.owner = p}) <= 1
      /\ Cardinality({x \in statuses : x.owner = p}) <= 1

IntentStable ==
  \A p \in Publishers : durable[p].phase # "empty" =>
    /\ durable[p].verified
    /\ durable[p].receipt = Receipt(durable[p].art)

=============================================================================
