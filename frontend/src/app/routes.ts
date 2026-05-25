import { createBrowserRouter } from "react-router";
import RootLayout from "./RootLayout";
import HomePage from "./pages/home";
import DetectionResultPage from "./pages/DetectionResultPage";
import GuidancePage from "./pages/GuidancePage";
import GuidanceDetailPage from "./pages/GuidanceDetailPage";
import LearningPage from "./pages/LearningPage";
import LearningDetailPage from "./pages/LearningDetailPage";
import PracticePage from "./pages/PracticePage";
import CasesPage from "./pages/CasesPage";
import CaseDetailPage from "./pages/CaseDetailPage";
import NotFoundPage from "./pages/NotFoundPage";
import DiscordBotPage from "./pages/DiscordBotPage";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: RootLayout,
    children: [
      { index: true, Component: HomePage },
      { path: "result", Component: DetectionResultPage },
      { path: "guidance", Component: GuidancePage },
      { path: "guidance/:scamType", Component: GuidanceDetailPage },
      { path: "learning", Component: LearningPage },
      { path: "learning/:scamType", Component: LearningDetailPage },
      { path: "practice", Component: PracticePage },
      { path: "quiz", Component: PracticePage },
      { path: "cases", Component: CasesPage },
      { path: "cases/:caseId", Component: CaseDetailPage },
      { path: "discord-bot", Component: DiscordBotPage },
      { path: "*", Component: NotFoundPage },
    ],
  },
]);
