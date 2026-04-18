export interface OnboardingState {
  name: string;
  role: string;
  areas: string[];
  hasOrg: boolean;
  orgName: string;
  orgSlug: string;
  model: string;
  apiProvider: string;
  apiKey: string;
  apiKeyLabel: string;
  apiKeySaved: boolean;
}

export interface StepProps {
  state: OnboardingState;
  onChange: (updates: Partial<OnboardingState>) => void;
  onNext: () => void;
  onBack: () => void;
}

export const INITIAL_STATE: OnboardingState = {
  name: "",
  role: "",
  areas: [],
  hasOrg: false,
  orgName: "",
  orgSlug: "",
  model: "",
  apiProvider: "",
  apiKey: "",
  apiKeyLabel: "",
  apiKeySaved: false,
};
