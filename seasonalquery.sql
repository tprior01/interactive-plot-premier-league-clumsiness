select 'minutes' as cat,
s8, s9, s10, s11, s12, s13, s14, s15, s16, s17, s18, s19, s20, s21, s22
from minutes
where PlayerID = :xid
union
select 'redcards' as cat,
s8, s9, s10, s11, s12, s13, s14, s15, s16, s17, s18, s19, s20, s21, s22
from redcards
where PlayerID = :xid
union
select 'pensconceded' as cat,
s8, s9, s10, s11, s12, s13, s14, s15, s16, s17, s18, s19, s20, s21, s22
from pensconceded
where PlayerID = :xid
union
select 'owngoals' as cat,
s8, s9, s10, s11, s12, s13, s14, s15, s16, s17, s18, s19, s20, s21, s22
from owngoals
where PlayerID = :xid
union
select 'errors' as cat,
s8, s9, s10, s11, s12, s13, s14, s15, s16, s17, s18, s19, s20, s21, s22
from errors
where PlayerID = :xid