import React, { useState } from "react";
import { JSONSchema7 } from "json-schema";
import { Form } from "@rjsf/bootstrap-4";
import { IChangeEvent } from "@rjsf/core";
import { RJSFSchema } from "@rjsf/utils";
import AJV8Validator from "@rjsf/validator-ajv8";
import SimpleEntityAPIClient, {
  SimpleEntityRequest,
  SimpleEntityResponse,
} from "../../APIClients/SimpleEntityAPIClient";

const schema: JSONSchema7 = {
  title: "Update Simple Entity",
  description: "A simple form to test updating a simple entity",
  type: "object",
  required: [
    "id",
    "stringField",
    "intField",
    "stringArrayField",
    "enumField",
    "boolField",
  ],
  properties: {
    id: {
      type: "string",
      title: "entity id",
      default: "123abc456def7890ghij1234",
    },
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

const SimpleEntityUpdateForm = (): React.ReactElement => {
  const [data, setData] = useState<SimpleEntityResponse | null>(null);
  const [formFields, setFormFields] = useState<SimpleEntityRequest | null>(
    null,
  );

  if (data) {
    return <p>Updated! ✔️</p>;
  }

  const onSubmit = async (data: IChangeEvent<SimpleEntityResponse>) => {
    if (data.formData) {
      const { id, ...entityData } = data.formData;
      const result = await SimpleEntityAPIClient.update(data.formData.id, {
        entityData,
      });
      setData(result);
    }
  };
  return (
    <Form
      formData={formFields}
      schema={schema as RJSFSchema}
      uiSchema={uiSchema}
      validator={AJV8Validator}
      onChange={(data: IChangeEvent<SimpleEntityRequest>) => {
        if (data.formData) {
          setFormFields(data.formData);
        }
      }}
      onSubmit={onSubmit}
    />
  );
};

export default SimpleEntityUpdateForm;
