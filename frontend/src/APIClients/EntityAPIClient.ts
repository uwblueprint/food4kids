import baseAPIClient from "./BaseAPIClient";
import AUTHENTICATED_USER_KEY from "../constants/AuthConstants";
import { getLocalStorageObjProperty } from "../utils/LocalStorageUtils";

enum EnumField {
  "A",
  "B",
  "C",
  "D",
}

export type EntityRequest = {
  stringField: string;
  intField: number;
  stringArrayField: string[];
  enumField: EnumField;
  boolField: boolean;
};

export type EntityResponse = {
  id: string | number;
  stringField: string;
  intField: number;
  stringArrayField: string[];
  enumField: EnumField;
  boolField: boolean;
};

const create = async ({
  formData,
}: {
  formData: EntityRequest;
}): Promise<EntityResponse | null> => {
  const bearerToken = `Bearer ${getLocalStorageObjProperty(
    AUTHENTICATED_USER_KEY,
    "accessToken",
  )}`;
  try {
    const { data } = await baseAPIClient.post("/entities", formData, {
      headers: { Authorization: bearerToken },
    });
    return data;
  } catch (error) {
    return null;
  }
};

const get = async (): Promise<EntityResponse[] | null> => {
  const bearerToken = `Bearer ${getLocalStorageObjProperty(
    AUTHENTICATED_USER_KEY,
    "accessToken",
  )}`;
  try {
    const { data } = await baseAPIClient.get("/entities", {
      headers: { Authorization: bearerToken },
    });
    return data;
  } catch (error) {
    return null;
  }
};

const getCSV = async (): Promise<string | null> => {
  const bearerToken = `Bearer ${getLocalStorageObjProperty(
    AUTHENTICATED_USER_KEY,
    "accessToken",
  )}`;
  try {
    const { data } = await baseAPIClient.get("/entities", {
      // Following line is necessary to set the Content-Type header
      // Reference: https://github.com/axios/axios/issues/86
      data: null,
      headers: { Authorization: bearerToken, "Content-Type": "text/csv" },
    });

    return data;
  } catch (error) {
    return null;
  }
};

const update = async (
  id: number | string,
  {
    entityData,
  }: {
    entityData: EntityRequest;
  },
): Promise<EntityResponse | null> => {
  const bearerToken = `Bearer ${getLocalStorageObjProperty(
    AUTHENTICATED_USER_KEY,
    "accessToken",
  )}`;
  try {
    const { data } = await baseAPIClient.put(`/entities/${id}`, entityData, {
      headers: { Authorization: bearerToken },
    });
    return data;
  } catch (error) {
    return null;
  }
};

export default { create, get, getCSV, update };
