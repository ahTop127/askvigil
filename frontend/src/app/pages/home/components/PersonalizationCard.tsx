import { memo } from "react";
import { X, Bell } from "lucide-react";
import { Button } from "@components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@components/ui/dialog";
import { Label } from "@components/ui/label";
import { RadioGroup, RadioGroupItem } from "@components/ui/radio-group";
import type { UsePersonalizationReturn } from "../hooks/usePersonalization";
import { PERSONALIZATION_TOPICS } from "../hooks/usePersonalization";

export interface PersonalizationCardProps {
  p: UsePersonalizationReturn;
}

/**
 * Optional onboarding strip + dialog for topics, goals, and alerts.
 */
export const PersonalizationCard = memo(function PersonalizationCard({
  p,
}: PersonalizationCardProps) {
  if (!p.showCard && !p.showDialog) return null;

  return (
    <>
      {p.showCard && !p.showDialog && (
        <div
          className="fixed bottom-4 left-4 right-4 z-50 md:left-auto md:right-6 md:max-w-md rounded-2xl border border-primary/40 bg-card/95 backdrop-blur-md shadow-xl p-4 flex flex-col gap-3"
          role="dialog"
          aria-label="Personalize your experience"
        >
          <div className="flex justify-between items-start gap-2">
            <div>
              <p className="font-semibold text-[#213034] flex items-center gap-2">
                <Bell className="w-4 h-4 text-primary" aria-hidden />
                Personalize AskVigil
              </p>
              <p className="text-sm text-gray-600 mt-1">
                Tell us what you care about so we can tailor tips (stored on
                this device only).
              </p>
            </div>
            <button
              type="button"
              onClick={p.dismissCard}
              className="text-gray-400 hover:text-gray-700 p-1"
              aria-label="Dismiss"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <div className="flex gap-2">
            <Button
              type="button"
              className="flex-1 bg-primary hover:bg-secondary text-primary-foreground"
              onClick={p.openDialog}
            >
              Set preferences
            </Button>
            <Button type="button" variant="outline" onClick={p.dismissCard}>
              Not now
            </Button>
          </div>
        </div>
      )}

      <Dialog
        open={p.showDialog}
        onOpenChange={(open) => !open && p.closeDialog()}
      >
        <DialogContent className="max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Your interests</DialogTitle>
            <DialogDescription>
              Select scam topics you want to learn more about.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 py-2">
            {PERSONALIZATION_TOPICS.map((topic) => (
              <label
                key={topic}
                className="flex items-center gap-2 text-sm cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={p.selectedTopics.includes(topic)}
                  onChange={() => p.toggleTopic(topic)}
                  className="rounded border-gray-300"
                />
                <span className="capitalize">{topic.replace(/-/g, " ")}</span>
              </label>
            ))}
          </div>

          <div className="space-y-2">
            <Label htmlFor="goal">Main goal</Label>
            <RadioGroup value={p.selectedGoal} onValueChange={p.setGoal}>
              <div className="flex items-center gap-2">
                <RadioGroupItem value="avoid" id="goal-avoid" />
                <Label htmlFor="goal-avoid">Avoid losing money</Label>
              </div>
              <div className="flex items-center gap-2">
                <RadioGroupItem value="recover" id="goal-recover" />
                <Label htmlFor="goal-recover">Recover from a scam</Label>
              </div>
              <div className="flex items-center gap-2">
                <RadioGroupItem value="learn" id="goal-learn" />
                <Label htmlFor="goal-learn">General learning</Label>
              </div>
            </RadioGroup>
          </div>

          <div className="space-y-2">
            <Label>Scam alerts</Label>
            <RadioGroup value={p.wantsAlerts} onValueChange={p.setWantsAlerts}>
              <div className="flex items-center gap-2">
                <RadioGroupItem value="yes" id="alerts-yes" />
                <Label htmlFor="alerts-yes">Yes, notify me</Label>
              </div>
              <div className="flex items-center gap-2">
                <RadioGroupItem value="no" id="alerts-no" />
                <Label htmlFor="alerts-no">No thanks</Label>
              </div>
            </RadioGroup>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={p.closeDialog}>
              Cancel
            </Button>
            <Button
              className="bg-primary hover:bg-secondary text-primary-foreground"
              onClick={() => void p.savePreferences()}
            >
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
});
