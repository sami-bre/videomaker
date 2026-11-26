import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Docs } from "./Docs";
import { followSystemTheme } from "./theme";
import "./index.css";

followSystemTheme();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Docs />
  </StrictMode>,
);
