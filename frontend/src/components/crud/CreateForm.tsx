import React, { useState } from "react";
// import { decamelizeKeys } from "humps";
import { JSONSchema7 } from "json-schema";
import { Form } from "@rjsf/bootstrap-4";
import EntityAPIClient, {
  EntityRequest,
  EntityResponse,
} from "../../APIClients/EntityAPIClient";

const schema: JSONSchema7 = {
  title: "Create Entity",
  description: "A simple form to test creating an entity",
  type: "object",
  required: [
    "stringField",
    "intField",
    "stringArrayField",
    "enumField",
    "boolField",
  ],
  properties: {
    stringField: {
      type: "string",
      title: "String Field",
      default: "UW Blueprint",
    },
    intField: {
      type: "integer",
      title: "Integer Field",
      default: 2017,
    },
    stringArrayField: {
      type: "array",
      items: {
        type: "string",
      },
      title: "String Array Field",
      default: [],
    },
    enumField: {
      type: "string",
      enum: ["A", "B", "C", "D"],
      title: "Enum Field",
      default: "A",
    },
    boolField: {
      type: "boolean",
      title: "Boolean Field",
      default: true,
    },
  },
};

const uiSchema = {
  boolField: {
    "ui:widget": "select",
  },
};

const CreateForm = (): React.ReactElement => {
  const [data, setData] = useState<EntityResponse | null>(null);
  const [formFields, setFormFields] = useState<EntityRequest | null>(null);

  if (data) {
    return <p>Created! ✔️</p>;
  }

  const onSubmit = async ({ formData }: { formData: EntityRequest }) => {
    const result = await EntityAPIClient.create({ formData });
    setData(result);
  };
  return (
    <Form
      formData={formFields}
      schema={schema}
      uiSchema={uiSchema}
      onChange={({ formData }: { formData: EntityRequest }) =>
        setFormFields(formData)
      }
      onSubmit={onSubmit}
    />
  );
};

export default CreateForm;
