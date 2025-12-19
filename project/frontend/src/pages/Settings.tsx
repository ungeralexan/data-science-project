// src/pages/Settings.tsx
import { useState, useEffect } from 'react';

import { Typography, Form, Input, Button, Card, Space, Divider, Select, App, Switch } from 'antd';
import { MailOutlined, LockOutlined, UserOutlined, ExclamationCircleOutlined, BulbOutlined } from '@ant-design/icons';

import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useTheme } from '../hooks/useTheme';
import { POSSIBLE_INTEREST_KEYWORDS } from '../config';
import '../components/css/Settings.css';

/*
    This is the Settings page component that allows users to manage their profile information,
    change their password, update their interests, and delete their account.

    Functions:

    - handleProfileUpdate: Handles updating the user's profile information such as name and email.
    - handlePasswordChange: Handles changing the user's password.
    - handleInterestsUpdate: Handles updating the user's interests based on selected keywords and text.
    - handleDeleteAccount: Handles the deletion of the user's account with a confirmation modal.


*/

const { Title, Text } = Typography;

// ----- Interfaces for form values -----
interface ProfileFormValues {
    first_name: string;
    last_name: string;
    email: string;
}

interface InterestsFormValues {
    interest_keys: string[];
    interest_text: string;
}

interface PasswordFormValues {
    password: string;
    confirmPassword: string;
}

const INTEREST_KEYWORDS = POSSIBLE_INTEREST_KEYWORDS;


// ----- Component -----

function SettingsContent() {

    // ----- State and hooks -----

    // Authentication context and navigation
    const { user, updateUser, deleteAccount, triggerRecommendations, isRecommendationLoading, recommendationCooldownRemaining } = useAuth();
    const { theme, toggleTheme } = useTheme();
    const navigate = useNavigate();
    const { message: messageApi, modal } = App.useApp();
    
    const [profileLoading, setProfileLoading] = useState(false);
    const [passwordLoading, setPasswordLoading] = useState(false);
    const [interestsLoading, setInterestsLoading] = useState(false);
    const [deleteLoading, setDeleteLoading] = useState(false);
    
    const [profileForm] = Form.useForm();
    const [passwordForm] = Form.useForm();
    const [interestsForm] = Form.useForm();

    // Update form values when user changes (fixes stale data after navigation)
    useEffect(() => {
        if (user) {
            profileForm.setFieldsValue({
                first_name: user.first_name || '',
                last_name: user.last_name || '',
                email: user.email || '',
            });

            interestsForm.setFieldsValue({
                interest_keys: user.interest_keys || [],
                interest_text: user.interest_text || '',
            });
        }
    }, [user, profileForm, interestsForm]);

    // ----- Functions -----

    // Handle profile update
    const handleProfileUpdate = async (values: ProfileFormValues) => {
        setProfileLoading(true);

        try {

            await updateUser({
                first_name: values.first_name,
                last_name: values.last_name,
                email: values.email,
            });

            messageApi.success('Profile updated successfully!');
        } catch (error) {
            messageApi.error(error instanceof Error ? error.message : 'Failed to update profile');
        } finally {
            setProfileLoading(false);
        }
    };

    // Handle password change
    const handlePasswordChange = async (values: PasswordFormValues) => {

        setPasswordLoading(true);

        try {

            await updateUser({
                password: values.password,
            });

            messageApi.success('Password changed successfully!');
            passwordForm.resetFields();
        } catch (error) {
            messageApi.error(error instanceof Error ? error.message : 'Failed to change password');
        } finally {
            setPasswordLoading(false);
        }
    };

    // Handle interests update
    const handleInterestsUpdate = async (values: InterestsFormValues) => {
        setInterestsLoading(true);
        
        try {

            await updateUser({
                interest_keys: values.interest_keys || [],
                interest_text: values.interest_text || '',
            });

            messageApi.success('Interests updated successfully!');
            
            // Trigger on-demand event recommendations
            messageApi.info('Generating personalized event recommendations...');

            try {
                await triggerRecommendations();
                messageApi.success('Event recommendations updated!');
            } catch (recError) {
                console.error('Error generating recommendations:', recError);
                messageApi.warning('Could not generate recommendations. Please try again later.');
            }
        } catch (error) {
            messageApi.error(error instanceof Error ? error.message : 'Failed to update interests');
        } finally {
            setInterestsLoading(false);
        }
    };

    // Handle account deletion
    const handleDeleteAccount = () => {

        // Show confirmation modal before deleting account
        modal.confirm({
            title: 'Are you sure you want to delete your account?',
            icon: <ExclamationCircleOutlined />,
            content: 'This action cannot be undone. All your data will be permanently deleted.',
            okText: 'Yes, delete my account',
            okType: 'danger',
            cancelText: 'Cancel',

            onOk: async () => {
                setDeleteLoading(true);

                try {
                    await deleteAccount();
                    messageApi.success('Account deleted successfully');
                    navigate('/login');

                } catch (error) {
                    messageApi.error(error instanceof Error ? error.message : 'Failed to delete account');
                } finally {
                    setDeleteLoading(false);
                }
            },
        });
    };

    // ----- Rendering of Settings Page -----

    return (
        <div className="settings-container">
            <Title level={2}>Settings</Title>
            
            <Space direction="vertical" size="large" className="settings-space-full-width">
                {/* Profile Information Card */}
                <Card title="Profile Information">
                    <Form
                        form={profileForm}
                        layout="vertical"
                        onFinish={handleProfileUpdate}
                        
                        initialValues={{
                            first_name: user?.first_name || '',
                            last_name: user?.last_name || '',
                            email: user?.email || '',
                        }}
                    >
                        <Form.Item
                            name="first_name"
                            label="First Name"
                            rules={[{ required: true, message: 'Please enter your first name' }]}
                        >
                            <Input prefix={<UserOutlined />} placeholder="First Name" />
                        </Form.Item>

                        <Form.Item
                            name="last_name"
                            label="Last Name"
                            rules={[{ required: true, message: 'Please enter your last name' }]}
                        >
                            <Input prefix={<UserOutlined />} placeholder="Last Name" />
                        </Form.Item>

                        <Form.Item
                            name="email"
                            label="Email"
                            rules={[
                                { required: true, message: 'Please enter your email' },
                                { type: 'email', message: 'Please enter a valid email' },
                            ]}
                        >
                            <Input prefix={<MailOutlined />} placeholder="Email" />
                        </Form.Item>

                        <Form.Item>
                            <Button type="primary" htmlType="submit" loading={profileLoading}>
                                Update Profile
                            </Button>
                        </Form.Item>
                    </Form>
                </Card>

                {/* Appearance Card - Dark Mode Toggle */}
                <Card title="Appearance">
                    <div className="settings-appearance-row">
                        <div className="settings-appearance-info">
                            <Space>
                                <BulbOutlined />
                                <Text strong>Dark Mode</Text>
                            </Space>
                            <br />
                            <Text type="secondary">
                                Switch between light and dark theme
                            </Text>
                        </div>
                        <Switch
                            checked={theme === 'dark'}
                            onChange={toggleTheme}
                            checkedChildren="Dark"
                            unCheckedChildren="Light"
                        />
                    </div>
                </Card>

                {/* Interests Card */}
                <Card title="Interests">
                    <Form
                        form={interestsForm}
                        layout="vertical"
                        onFinish={handleInterestsUpdate}

                        initialValues={{
                            interest_keys: user?.interest_keys || [],
                            interest_text: user?.interest_text || '',
                        }}
                    >
                        <Form.Item
                            name="interest_keys"
                            label="Interest Keywords"
                            extra="Select one or more keywords that match your interests"
                        >
                            <Select
                                mode="multiple"
                                placeholder="Select your interests"
                                options={INTEREST_KEYWORDS.map(keyword => ({ 
                                    label: keyword, 
                                    value: keyword 
                                }))}
                                allowClear
                            />
                        </Form.Item>

                        <Form.Item
                            name="interest_text"
                            label="Interest Description"
                            extra="Describe your interests in more detail"
                        >
                            <Input.TextArea 
                                rows={4} 
                                placeholder="Describe your interests..." 
                            />
                        </Form.Item>

                        <Form.Item>
                            <Button 
                                type="primary" 
                                htmlType="submit" 
                                loading={interestsLoading || isRecommendationLoading}
                                disabled={recommendationCooldownRemaining > 0 || isRecommendationLoading}
                            >
                                {recommendationCooldownRemaining > 0 
                                    ? `Please wait ${recommendationCooldownRemaining}s` 
                                    : isRecommendationLoading 
                                        ? 'Generating Recommendations...'
                                        : 'Update Interests'}
                            </Button>
                        </Form.Item>
                    </Form>
                </Card>

                {/* Change Password Card */}
                <Card title="Change Password">
                    <Form
                        form={passwordForm}
                        layout="vertical"
                        onFinish={handlePasswordChange}
                    >
                        <Form.Item
                            name="password"
                            label="New Password"
                            rules={[
                                { required: true, message: 'Please enter a new password' },
                                { min: 6, message: 'Password must be at least 6 characters' },
                            ]}
                        >
                            <Input.Password prefix={<LockOutlined />} placeholder="New Password" />
                        </Form.Item>

                        <Form.Item
                            name="confirmPassword"
                            label="Confirm New Password"
                            dependencies={['password']}

                            rules={[
                                { required: true, message: 'Please confirm your new password' },
                                ({ getFieldValue }) => ({
                                    validator(_, value) {
                                        if (!value || getFieldValue('password') === value) {
                                            return Promise.resolve();
                                        }
                                        return Promise.reject(new Error('Passwords do not match'));
                                    },
                                }),
                            ]}
                        >
                            <Input.Password prefix={<LockOutlined />} placeholder="Confirm New Password" />
                        </Form.Item>

                        <Form.Item>
                            <Button type="primary" htmlType="submit" loading={passwordLoading}>
                                Change Password
                            </Button>
                        </Form.Item>
                    </Form>
                </Card>

                {/* Danger Zone Card */}
                <Card 
                    title={<Text type="danger">Danger Zone</Text>}
                    className="settings-danger-card"
                >
                    <Space direction="vertical" size="middle" className="settings-space-full-width">
                        <div>
                            <Text strong>Delete Account</Text>
                            <br />
                            <Text type="secondary">
                                Once you delete your account, there is no going back. Please be certain.
                            </Text>
                        </div>

                        <Divider className="settings-danger-divider" />

                        <Button 
                            danger 
                            type="primary" 
                            onClick={handleDeleteAccount}
                            loading={deleteLoading}
                        >
                            Delete My Account
                        </Button>
                    </Space>
                </Card>
            </Space>
        </div>
    );
}

// Wrap with App component to enable modal and message hooks
export default function Settings() {
    return (
        <App>
            <SettingsContent />
        </App>
    );
}