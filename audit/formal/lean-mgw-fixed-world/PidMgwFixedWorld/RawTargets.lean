import PidMgwFixedWorld.Contract

/-! Frozen propositions only; no solution proofs are present. -/

set_option autoImplicit false
set_option warningAsError true

open scoped BigOperators
open PidFiniteConvergence

namespace PidMgwFixedWorld.RawTargets

def WorldNormalization : Prop :=
  ∑ w : World, worldMass w = 1

def WorldMarginals : Prop :=
  ∀ b : Fin 2, worldAMass b = 1 / 2 ∧ worldBMass b = 1 / 2 ∧ worldUMass b = 1 / 2

def WorldFactorization : Prop :=
  ∀ w : World, worldMass w = worldAMass w.1 * worldBMass w.2.1 * worldUMass w.2.2

def ObservationIdentity : Prop :=
  ∀ (tag : AddedSource) (w : World),
    (observe tag w).1 0 = w.1 ∧
    (observe tag w).1 1 = addedValue tag w ∧
    (observe tag w).2 = (w.1, w.2.1)

def CountTable : Prop :=
  ∀ (tag : AddedSource) (z : Key), count tag z = expectedCount tag z

def Totals : Prop :=
  ∀ tag : AddedSource, totalCount (count tag) = 8

def Nonnegative : Prop :=
  ∀ (tag : AddedSource) (z : Key), 0 ≤ jointLaw tag z

def Normalization : Prop :=
  ∀ tag : AddedSource, ∑ z : Key, jointLaw tag z = 1

def Pushforward : Prop :=
  ∀ (tag : AddedSource) (z : Key), jointLaw tag z = pushedLaw tag z

def SourceMasses : Prop :=
  ∀ (tag : AddedSource) (z : Key),
    finiteEventMass (jointLaw tag) (sxPid2SourceEvent .sourceOne z) = 1 / 2 ∧
    finiteEventMass (jointLaw tag) (sxPid2SourceEvent .sourceTwo z) = 1 / 2 ∧
    finiteEventMass (jointLaw tag) (sxPid2SourceEvent .jointSources z) = 1 / 4

def EventCounts : Prop :=
  ∀ (tag : AddedSource) (z : Key), 0 < count tag z →
    eventCount (count tag) (targetBranchEvent z) = 2 ∧
    ∀ node : SxPid2Node,
      eventCount (count tag) (sxPid2SourceEvent node z) = expectedSourceCount node ∧
      eventCount (count tag) (sxPid2TargetRestrictedEvent node z) =
        expectedRestrictedCount tag node

def NetArguments : Prop :=
  ∀ (tag : AddedSource) (z : Key), 0 < count tag z →
    ∀ node : SxPid2Node,
      countNetArgument (count tag) node z = expectedNetArgument tag node

def IrrelevantAverages : Prop :=
  ∀ node : SxPid2Node,
    averagedCumulativeComponent (jointLaw .irrelevant) .net node =
      expectedAverage .irrelevant node

def CompletingAverages : Prop :=
  ∀ node : SxPid2Node,
    averagedCumulativeComponent (jointLaw .completing) .net node =
      expectedAverage .completing node

def IrrelevantSynergy : Prop :=
  synergy .irrelevant = Real.log (4 / 3)

def CompletingSynergy : Prop :=
  synergy .completing = Real.log (4 / 3)

def ConditionalRatio : Prop :=
  ∀ (tag : AddedSource) (z : Key), 0 < count tag z →
    0 < finiteEventMass (jointLaw tag) (sxPid2SourceEvent .sourceOne z) ∧
    0 < finiteEventMass (jointLaw tag) (sxPid2SourceEvent .jointSources z) ∧
    0 < finiteEventMass (jointLaw tag) (sxPid2TargetRestrictedEvent .sourceOne z) ∧
    conditionalRatio tag z = (match tag with | .irrelevant => 1 | .completing => 2)

def IrrelevantCmi : Prop :=
  directCmi .irrelevant = 0

def CompletingCmi : Prop :=
  directCmi .completing = Real.log 2

def SynergyEqual : Prop :=
  synergy .irrelevant = synergy .completing

def CmiDifferent : Prop :=
  directCmi .irrelevant ≠ directCmi .completing

end PidMgwFixedWorld.RawTargets

