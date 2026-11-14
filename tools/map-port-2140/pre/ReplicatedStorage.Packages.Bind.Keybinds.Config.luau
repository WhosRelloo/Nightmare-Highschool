
type KeyCodes = string

-- Each action's inputs: the keyboard / mouse key first (Settings rebinds it, and touch buttons press it), then the
-- gamepad button (fixed). Sprint and Crouch / Slide are toggles on a gamepad (L3 / R3), in Controllers.Gui.GamepadControls.
return {

	Began = {
		Feint = { `MouseButton2`, `ButtonL1` };
		Slide = { `LeftControl` }; -- slide while sprinting, otherwise hold to crouch

		M1 = { `MouseButton1`, `ButtonR2` };
		M2 = { `R`, `ButtonR1` };

		Dodge = { `Q`, `ButtonB` };
		Sprint = { `LeftShift` }; -- hold to sprint

		Block = { `F`, `ButtonL2` };
		Equip = { `E`, `ButtonX` };

		Jump = { `Space` };

		Carry = { `V`, `ButtonY` };
		Grip = { `B`, `DPadUp` };

	};

	Ended = { Sprint = { `LeftShift` }; Block = { `F`, `ButtonL2` }; Slide = { `LeftControl` }; };
}
