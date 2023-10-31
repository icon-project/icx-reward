class EventSig:
    Penalty = "PenaltyImposed(Address,int,int)"
    Slash = "Slashed(Address,Address,int)"
    SetBond = "BondSet(Address,bytes)"
    SetDelegation = "DelegationSet(Address,bytes)"
    VOTE_SIG_LIST = [SetBond, SetDelegation]

