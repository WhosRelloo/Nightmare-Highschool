--[[
	Electives (shared). One pick per term at the Registrar (Services.School.Electives); it fills
	Config.Classes.ElectiveSlots (Tue/Thu, periods 3 and 4). Only Open electives can be picked.
	Closed ones show "Opens in a later term" on the Registrar board; their Room is a placeholder until their spec.
]]
local Electives = {}

Electives.List = {
	Anatomy     = { Id = `Anatomy`;     Name = `Anatomy`;     Room = `R103`; Teacher = `Mr. Sallow`; Open = true;  Order = 1 };
	Workshop    = { Id = `Workshop`;    Name = `Workshop`;    Room = `R103`; Teacher = ``; Open = false; Order = 2 };
	Photography = { Id = `Photography`; Name = `Photography`; Room = `R103`; Teacher = ``; Open = false; Order = 3 };
	Ceramics    = { Id = `Ceramics`;    Name = `Ceramics`;    Room = `R103`; Teacher = ``; Open = false; Order = 4 };
	Herbology   = { Id = `Herbology`;   Name = `Herbology`;   Room = `R103`; Teacher = ``; Open = false; Order = 5 };
	HomeEc      = { Id = `HomeEc`;      Name = `Home Ec`;     Room = `R103`; Teacher = ``; Open = false; Order = 6 };
	Sewing      = { Id = `Sewing`;      Name = `Sewing`;      Room = `R103`; Teacher = ``; Open = false; Order = 7 };
	Art         = { Id = `Art`;         Name = `Art`;         Room = `R103`; Teacher = ``; Open = false; Order = 8 };
	PE          = { Id = `PE`;          Name = `PE`;          Room = `R103`; Teacher = ``; Open = false; Order = 9 };
	Theatre     = { Id = `Theatre`;     Name = `Theatre`;     Room = `R103`; Teacher = ``; Open = false; Order = 10 };
}

function Electives.Get(Id: string?)
	return if typeof(Id) == `string` then Electives.List[Id] else nil
end

return Electives
