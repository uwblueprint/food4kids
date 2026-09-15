import { createContext } from 'react';

/** Element popover panels portal into; null falls back to document.body. */
export const PopupContainerContext = createContext<HTMLElement | null>(null);
