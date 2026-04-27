import {
  Button,
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/common/components';

import { SectionHeader } from '../components/SectionHeader';
import { SpecNote } from '../components/SpecNote';

export function DialogSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Dialog</SectionHeader>

      <div className="mb-10 space-y-6">
        <SpecNote title="Composition">
          Built with Radix UI Dialog primitives using a composable shadcn-style
          API: Dialog › DialogTrigger › DialogContent › DialogHeader +
          DialogFooter. An X close button is auto-included in DialogContent.
        </SpecNote>

        <SpecNote title="Backdrop">
          A semi-transparent overlay fades in behind the dialog to focus
          attention. Clicking the overlay or pressing Escape closes the dialog.
        </SpecNote>

        <SpecNote title="Max Width">
          DialogContent is capped at 600px wide and centers on the viewport.
        </SpecNote>

        <SpecNote title="Actions">
          DialogFooter holds Cancel (secondary) and a CTA (primary/destructive)
          button. The CTA label and variant should reflect the action, e.g.
          "Delete" in red, "Save" in blue.
        </SpecNote>
      </div>

      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
        <div className="divide-grey-300 grid grid-cols-1 divide-y md:grid-cols-2 md:divide-x md:divide-y-0">
          <div className="flex flex-col gap-6 p-6">
            <p className="text-p3 font-semibold tracking-wider text-blue-300 uppercase">
              Confirm Action
            </p>
            <Dialog>
              <DialogTrigger asChild>
                <Button variant="primary">Open Confirm Dialog</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Save Changes?</DialogTitle>
                  <DialogDescription>
                    Your changes will be applied and saved. This action can be
                    undone later.
                  </DialogDescription>
                </DialogHeader>
                <DialogFooter>
                  <DialogClose asChild>
                    <Button variant="secondary">Cancel</Button>
                  </DialogClose>
                  <DialogClose asChild>
                    <Button variant="primary">Save Changes</Button>
                  </DialogClose>
                </DialogFooter>
              </DialogContent>
            </Dialog>
            <p className="text-p3 text-grey-400">
              Standard confirmation with cancel + primary CTA.
            </p>
          </div>

          <div className="flex flex-col gap-6 p-6">
            <p className="text-p3 font-semibold tracking-wider text-blue-300 uppercase">
              Destructive Action
            </p>
            <Dialog>
              <DialogTrigger asChild>
                <Button variant="primary">Open Destructive Dialog</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Leave Without Saving?</DialogTitle>
                  <DialogDescription>
                    Any unsaved changes will be lost. This action cannot be
                    undone.
                  </DialogDescription>
                </DialogHeader>
                <DialogFooter>
                  <DialogClose asChild>
                    <Button variant="secondary">Stay</Button>
                  </DialogClose>
                  <DialogClose asChild>
                    <Button variant="primary">Leave</Button>
                  </DialogClose>
                </DialogFooter>
              </DialogContent>
            </Dialog>
            <p className="text-p3 text-grey-400">
              Destructive variant — warn before an irreversible action.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
