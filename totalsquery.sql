select PlayerID, PlayerName, PlayerShortName, Position, minutes, redcards, errors, pensconceded, owngoals,
       (redcards + errors + pensconceded + owngoals) as sumerrors
    from
    (select PlayerID, PlayerName, PlayerShortName, Position from names)
    join
    (select PlayerID, sum as minutes from minutes)
    using(PlayerID)
    join
    (select PlayerID, sum as errors from errors)
    using(PlayerID)
    join
    (select PlayerID, sum as redcards from redcards)
    using(PlayerID)
    join
    (select PlayerID, sum as pensconceded from pensconceded)
    using(PlayerID)
    join
    (select PlayerID, sum as owngoals from owngoals)
    using(PlayerID)
