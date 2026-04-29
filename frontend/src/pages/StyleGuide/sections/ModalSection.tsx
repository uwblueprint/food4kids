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

import { ComponentPreview } from '../components/ComponentPreview';
import { CompositionTree } from '../components/CompositionTree';
import { SectionDescription } from '../components/SectionDescription';
import { SectionHeader } from '../components/SectionHeader';
import { SpecNote } from '../components/SpecNote';

const MODAL_TREE = `Modal
├─ ModalTrigger
└─ ModalContent
    ├─ ModalHeader
    │   ├─ ModalTitle
    │   └─ ModalDescription
    ├─ [slot: content]
    ├─ ModalFooter
    └─ ModalClose`;

const MODAL_CONFIRM_CODE = `import {
  Button, Modal, ModalClose, ModalContent,
  ModalDescription, ModalFooter, ModalHeader,
  ModalTitle, ModalTrigger,
} from '@/common/components';

<Modal>
  <ModalTrigger asChild>
    <Button variant="primary">Open Modal</Button>
  </ModalTrigger>
  <ModalContent>
    <ModalHeader>
      <ModalTitle>Save Changes?</ModalTitle>
      <ModalDescription>
        Your changes will be applied and saved.
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
</Modal>`;


export function ModalSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Modal</SectionHeader>
      <SectionDescription>
        Composable dialog built on Radix UI Dialog primitives.{' '}
        <code className="text-p2 rounded bg-grey-150 px-1">ModalContent</code>{' '}
        includes an X close button automatically; use{' '}
        <code className="text-p2 rounded bg-grey-150 px-1">ModalTrigger</code> to
        open it or control the{' '}
        <code className="text-p2 rounded bg-grey-150 px-1">open</code> prop
        directly for programmatic control.
      </SectionDescription>

      <div className="mb-10 space-y-6">
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

      <p className="text-p3 mb-2 font-semibold tracking-wider text-grey-400 uppercase">
        Composition
      </p>
      <div className="mb-8">
        <CompositionTree tree={MODAL_TREE} />
      </div>

      <p className="text-p3 mb-2 font-semibold tracking-wider text-grey-400 uppercase">
        Usage
      </p>
      <div className="space-y-6">
        <ComponentPreview title="Confirm Action" code={MODAL_CONFIRM_CODE}>
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
        </ComponentPreview>

      </div>
    </section>
  );
}
