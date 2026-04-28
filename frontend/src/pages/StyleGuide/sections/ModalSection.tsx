import {
  Button,
  Modal,
  ModalClose,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
  ModalTrigger,
} from '@/common/components';

import { SectionHeader } from '../components/SectionHeader';
import { SpecNote } from '../components/SpecNote';

export function ModalSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Modal</SectionHeader>

      <div className="mb-10 space-y-6">
        <SpecNote title="Composition">
          Built with Radix UI Dialog primitives using a composable shadcn-style
          API: Modal › ModalTrigger › ModalContent › ModalHeader +
          ModalFooter. An X close button is auto-included in ModalContent.
        </SpecNote>

        <SpecNote title="Backdrop">
          A semi-transparent overlay fades in behind the modal to focus
          attention. Clicking the overlay or pressing Escape closes the modal.
        </SpecNote>

        <SpecNote title="Max Width">
          ModalContent is capped at 600px wide and centers on the viewport.
        </SpecNote>

        <SpecNote title="Actions">
          ModalFooter holds Cancel (secondary) and a CTA (primary/destructive)
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
            <Modal>
              <ModalTrigger asChild>
                <Button variant="primary">Open Confirm Modal</Button>
              </ModalTrigger>
              <ModalContent>
                <ModalHeader>
                  <ModalTitle>Save Changes?</ModalTitle>
                  <ModalDescription>
                    Your changes will be applied and saved. This action can be
                    undone later.
                  </ModalDescription>
                </ModalHeader>
                <ModalFooter>
                  <ModalClose asChild>
                    <Button variant="secondary">Cancel</Button>
                  </ModalClose>
                  <ModalClose asChild>
                    <Button variant="primary">Save Changes</Button>
                  </ModalClose>
                </ModalFooter>
              </ModalContent>
            </Modal>
            <p className="text-p3 text-grey-400">
              Standard confirmation with cancel + primary CTA.
            </p>
          </div>

          <div className="flex flex-col gap-6 p-6">
            <p className="text-p3 font-semibold tracking-wider text-blue-300 uppercase">
              Destructive Action
            </p>
            <Modal>
              <ModalTrigger asChild>
                <Button variant="primary">Open Destructive Modal</Button>
              </ModalTrigger>
              <ModalContent>
                <ModalHeader>
                  <ModalTitle>Leave Without Saving?</ModalTitle>
                  <ModalDescription>
                    Any unsaved changes will be lost. This action cannot be
                    undone.
                  </ModalDescription>
                </ModalHeader>
                <ModalFooter>
                  <ModalClose asChild>
                    <Button variant="secondary">Stay</Button>
                  </ModalClose>
                  <ModalClose asChild>
                    <Button variant="primary">Leave</Button>
                  </ModalClose>
                </ModalFooter>
              </ModalContent>
            </Modal>
            <p className="text-p3 text-grey-400">
              Destructive variant — warn before an irreversible action.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
