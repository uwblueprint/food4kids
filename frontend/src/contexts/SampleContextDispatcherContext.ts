import React, { createContext } from "react";
import { SampleContextAction } from "../types/SampleContextTypes";

const SampleContextDispatcherContext = createContext<
  React.Dispatch<SampleContextAction>
>(() => {
  // This is a placeholder implementation for the context default value
});

export default SampleContextDispatcherContext;
