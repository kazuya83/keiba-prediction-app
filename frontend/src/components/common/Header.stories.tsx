import type { Meta, StoryObj } from "@storybook/react";
import { Header } from "./Header";
import { BrowserRouter } from "react-router-dom";

const meta: Meta<typeof Header> = {
  title: "Common/Header",
  component: Header,
  tags: ["autodocs"],
  decorators: [
    (Story) => (
      <BrowserRouter>
        <Story />
      </BrowserRouter>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof Header>;

export const Default: Story = {};

