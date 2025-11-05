import type { InjectionKey, Ref } from 'vue'

export type RangeBin = { id: number; min: number; max: number; mass: number };
export type GenderBin = { id: number; label: string; mass: number };

export type PersonaConfig = {
  numSubjects: number; // >= 1
  generalIntent: string; // non-empty
  examplePersona: string;
  // Unified demographics schema
  demographics: {
    name: string;
    choices: { name: string; weight: number }[]; // now use weight instead of probability
  }[];
  // Legacy fields kept optional for backward compatibility
  agePmf?: Record<`${number}-${number}`, number>;
  genderPmf?: Record<string, number>;
  incomePmf?: Record<`${number}-${number}`, number>;
};

export type ExperimentConfig = {
  startUrl: string;
  headless: boolean;
  maxSteps: number; // [1..5000]
  concurrency: number;
};

export type SurveyConfig = {
  questionnaire: string; // raw JSON string from textarea
};

export type WizardForm = {
  experiment: ExperimentConfig;
  survey: SurveyConfig;
  persona: PersonaConfig;
};

export interface WizardNav {
  current: Ref<number>
  steps: number
  next: () => void
  prev: () => void
  finish: () => void
}

export const FORM_KEY: InjectionKey<WizardForm> = Symbol('WizardForm')
export const NAV_KEY: InjectionKey<WizardNav> = Symbol('WizardNav')
