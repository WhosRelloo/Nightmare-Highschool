
---| Type Annotation |---

type 		Registry = {};
type 		Util = { [string]: any };

export type Dispatcher = {
	Cmdr: CmdrClient;
	Run: (self: Dispatcher, ...string) -> ();
	
	EvaluateAndRun: (self: Dispatcher, commandText: string, executor: Player?, options: { Data: any?, IsHuman: boolean? }?) -> ();
	GetHistory: (self: Dispatcher) -> { string };
};

export type CmdrClient = {
	Registry: Registry;
	Dispatcher: Dispatcher;
	Util: Util;

	Enabled: boolean;
	PlaceName: string;
	ActivationKeys: { [Enum.KeyCode]: true };

	SetActivationKeys: (self: CmdrClient, keys: { Enum.KeyCode }) -> ();
	SetPlaceName: (self: CmdrClient, labelText: string) -> ();
	SetEnabled: (self: CmdrClient, isEnabled: boolean) -> ();

	Show: (self: CmdrClient) -> ();
	Hide: (self: CmdrClient) -> ();
	Toggle: (self: CmdrClient) -> ();

	HandleEvent: (self: CmdrClient, event: string, handler: (...any) -> any) -> ();

	SetMashToEnable: (self: CmdrClient, isEnabled: boolean) -> ();
	SetActivationUnlocksMouse: (self: CmdrClient, isEnabled: boolean) -> ();
	SetHideOnLostFocus: (self: CmdrClient, isEnabled: boolean) -> ();
};

---| Permission Config |---

return {
	
	Owner = {
		4283953723; --/ VanitasSano_o
		1219061975; --/ zz
		3585755651; --//
	};
	
	Admin = {
		4283953723; --/ VanitasSano_o
		1219061975; --/ zz
		3585755651 --// zoac
	};

	-- (console 1a) testers: level 2 (the Test side) in live servers, no moderation beyond level 1's
	Testers = {
	};
	
	
	WhiteListedDevices = { Enum.PreferredInput.KeyboardAndMouse; Enum.PreferredInput.Gamepad }
} :: {
	Owner: { number };
	Admin: { number };
	Testers: { number };
	
	WhiteListedDevices: { Enum.PreferredInput };
}
