import { useState } from 'react';

import { useUpdateRoute } from '@/api/routes';
import EditIcon from '@/assets/icons/edit.svg?react';
import {
  Button,
  Field,
  FieldDescription,
  FieldLabel,
  Input,
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
  ModalTrigger,
} from '@/common/components';

interface RouteNameEditorProps {
  routeId: string;
  name: string;
}

function EditRouteNameForm({
  routeId,
  name,
  onClose,
  update,
}: RouteNameEditorProps & {
  onClose: () => void;
  update: ReturnType<typeof useUpdateRoute>;
}) {
  const [draft, setDraft] = useState(name);
  const trimmed = draft.trim();
  const invalid = !trimmed || trimmed.length > 255;

  return (
    <ModalContent className="w-[calc(100%-2rem)]">
      <form
        className="flex flex-col gap-6"
        onSubmit={(event) => {
          event.preventDefault();
          if (invalid || trimmed === name || update.isPending) return;
          update.mutate(
            { path: { route_id: routeId }, body: { name: trimmed } },
            { onSuccess: onClose }
          );
        }}
      >
        <ModalHeader>
          <ModalTitle variant="form">Edit route name</ModalTitle>
        </ModalHeader>
        <Field>
          <FieldLabel htmlFor="route-name" required>
            Route name
          </FieldLabel>
          <Input
            id="route-name"
            value={draft}
            maxLength={255}
            disabled={update.isPending}
            onChange={(event) => {
              setDraft(event.target.value);
              update.reset();
            }}
            aria-invalid={invalid}
            aria-describedby={invalid ? 'route-name-validation' : undefined}
          />
          {invalid && (
            <FieldDescription id="route-name-validation" error>
              Enter a route name between 1 and 255 characters.
            </FieldDescription>
          )}
        </Field>
        <div
          role="status"
          aria-atomic="true"
          className={update.isError ? '' : 'sr-only'}
        >
          {update.isError && (
            <FieldDescription error>
              Couldn&apos;t save the route name. Please try again.
            </FieldDescription>
          )}
        </div>
        <ModalFooter>
          <Button
            type="button"
            variant="tertiary"
            disabled={update.isPending}
            onClick={onClose}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={invalid || trimmed === name || update.isPending}
          >
            {update.isPending ? 'Saving…' : 'Save'}
          </Button>
        </ModalFooter>
      </form>
    </ModalContent>
  );
}

export function RouteNameEditor({ routeId, name }: RouteNameEditorProps) {
  const [open, setOpen] = useState(false);
  const update = useUpdateRoute();
  // Preserve the draft and block dismissal until an in-flight save completes.
  return (
    <Modal
      open={open}
      onOpenChange={(next) => {
        if (update.isPending) return;
        update.reset();
        setOpen(next);
      }}
    >
      <span className="text-h1 text-grey-500 min-w-0 font-bold break-words">
        {name || 'Route'}
      </span>
      <ModalTrigger asChild>
        <Button
          variant="ghost"
          shape="circular"
          aria-label="Edit route name"
          className="shrink-0"
        >
          <EditIcon className="size-5" />
        </Button>
      </ModalTrigger>
      {open && (
        <EditRouteNameForm
          update={update}
          routeId={routeId}
          name={name}
          onClose={() => setOpen(false)}
        />
      )}
    </Modal>
  );
}
