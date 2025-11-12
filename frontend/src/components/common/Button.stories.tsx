import type { Meta, StoryObj } from "@storybook/react";
import { Button } from "./Button";

const meta: Meta<typeof Button> = {
  title: "Common/Button",
  component: Button,
  tags: ["autodocs"],
  argTypes: {
    variant: {
      control: "select",
      options: ["primary", "secondary", "outline"],
    },
    size: {
      control: "select",
      options: ["sm", "md", "lg"],
    },
  },
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = {
  args: {
    children: "ボタン",
    variant: "primary",
  },
};

export const Secondary: Story = {
  args: {
    children: "ボタン",
    variant: "secondary",
  },
};

export const Outline: Story = {
  args: {
    children: "ボタン",
    variant: "outline",
  },
};

export const Small: Story = {
  args: {
    children: "小さいボタン",
    size: "sm",
  },
};

export const Large: Story = {
  args: {
    children: "大きいボタン",
    size: "lg",
  },
};

